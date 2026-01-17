import logging
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import F
from django.contrib.auth import get_user_model
import requests
import json
from django.conf import settings

from .models import RawWebhook, Transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def process_raw_webhook(webhook: RawWebhook) -> bool:
    """Process a stored RawWebhook. Returns True when processed successfully.

    This performs the same atomic handling as the live callback: finds the earliest
    pending Transaction matching the provider_reference, marks it completed,
    credits the user, marks other pending matches failed, links the webhook.
    """
    data = webhook.payload or {}
    merchant_request_id = data.get('MerchantRequestID') or data.get('merchant_request_id') or ''
    # MegaPay uses ResponseCode, but keep ResultCode check for backward compatibility
    result_code = data.get('ResponseCode') if data.get('ResponseCode') is not None else data.get('ResultCode')
    mpesa_receipt_number = data.get('TransactionReceipt') or data.get('MpesaReceiptNumber')
    transaction_reference = data.get('TransactionReference') or ''

    # ResponseCode 0 means success
    if result_code != 0:
        logger.info('Webhook %s has non-success ResponseCode=%s (%s)', 
                    webhook.pk, result_code, data.get('ResponseDescription', ''))
        
        # Try to find and mark the transaction as failed
        # First try by MerchantRequestID, then by TransactionReference
        txn = None
        if merchant_request_id:
            txn = Transaction.objects.filter(mpesa_code=merchant_request_id, status='pending').first()
        if not txn and transaction_reference:
            txn = Transaction.objects.filter(mpesa_code=transaction_reference, status='pending').first()
        
        if txn:
            txn.status = 'failed'
            txn.save(update_fields=['status'])
            webhook.transaction = txn
            logger.info('Marked transaction %s as failed due to ResponseCode %s', txn.pk, result_code)
        
        webhook.processed = True
        webhook.processed_at = timezone.now()
        webhook.save(update_fields=['transaction', 'processed', 'processed_at'])
        return False

    with db_transaction.atomic():
        # Try to find pending transaction in order of preference:
        # 1. TransactionReference (our original ref like COINS_...)
        # 2. TransactionID (MegaPay's PFXID)
        # 3. MerchantRequestID
        txn = None
        transaction_id = data.get('TransactionID') or ''
        
        # Our reference is stored in mpesa_code field
        if transaction_reference:
            pending_qs = Transaction.objects.select_for_update().filter(
                mpesa_code=transaction_reference,
                status='pending'
            ).order_by('created_at')
            txn = pending_qs.first()
            if txn:
                logger.info('Found transaction %s by TransactionReference: %s', txn.pk, transaction_reference)
        
        # Fallback to TransactionID (MegaPay's PFXID - may have been stored if we overwrote)
        if not txn and transaction_id:
            pending_qs = Transaction.objects.select_for_update().filter(
                mpesa_code=transaction_id,
                status='pending'
            ).order_by('created_at')
            txn = pending_qs.first()
            if txn:
                logger.info('Found transaction %s by TransactionID: %s', txn.pk, transaction_id)
        
        # Fallback to MerchantRequestID
        if not txn and merchant_request_id:
            pending_qs = Transaction.objects.select_for_update().filter(
                mpesa_code=merchant_request_id,
                status='pending'
            ).order_by('created_at')
            txn = pending_qs.first()
            if txn:
                logger.info('Found transaction %s by MerchantRequestID: %s', txn.pk, merchant_request_id)
        
        if not txn:
            logger.warning('No pending transaction found. TransactionRef=%s, TransactionID=%s, MerchantRequestID=%s', 
                          transaction_reference, transaction_id, merchant_request_id)
            # mark webhook processed for auditing so admin can inspect
            webhook.processed = True
            webhook.processed_at = timezone.now()
            webhook.save(update_fields=['processed', 'processed_at'])
            return False

        # Complete txn
        txn.status = 'completed'
        if mpesa_receipt_number:
            txn.mpesa_code = mpesa_receipt_number
        txn.completed_at = timezone.now()
        txn.save(update_fields=['status', 'mpesa_code', 'completed_at'])

        UserModel = get_user_model()
        UserModel.objects.filter(pk=txn.user_id).update(coins=F('coins') + txn.coins)

        extra = pending_qs.exclude(pk=txn.pk)
        if extra.exists():
            extra.update(status='failed')

        webhook.transaction = txn
        webhook.processed = True
        webhook.processed_at = timezone.now()
        webhook.save(update_fields=['transaction', 'processed', 'processed_at'])

        # Notify frontend via Channels so UI can update in real time
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                # Align with existing NotificationConsumer group naming
                group_name = f'notifications_{txn.user_id}'
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'payment_notification',
                        'event': 'transaction_completed',
                        'transaction_id': txn.pk,
                        'coins': txn.coins,
                        'amount': txn.amount,
                    }
                )
        except Exception:
            logger.exception('Failed to send websocket notification for txn %s', txn.pk)
        return True


def query_provider_status_for_txn(txn: Transaction) -> dict:
    """Query the provider for the status of a transaction.

    Returns a dict with at least keys: `status` (one of 'pending','completed','failed'),
    optional `result_code` (int) and `mpesa_receipt`.

    This implementation uses MEGAPAY_BASE_URL and MEGAPAY_API_KEY if configured.
    The provider endpoint and response parsing is best-effort and should be adapted
    to the real provider API schema.
    """
    base = getattr(settings, 'MEGAPAY_BASE_URL', None)
    key = getattr(settings, 'MEGAPAY_API_KEY', None)
    if not base:
        return {'status': 'unknown', 'error': 'no_provider_configured'}

    # Defensive: strip whitespace and normalize
    base = base.strip()
    url = f"{base.rstrip('/')}/mpesa/transaction-status"
    headers = {'Authorization': f'Bearer {key}'} if key else {}
    merchant_id = (txn.mpesa_code or '').strip()
    if not merchant_id:
        logger.warning('Transaction %s has empty mpesa_code; skipping provider query', txn.pk)
        return {'status': 'unknown', 'error': 'empty_merchant_request_id'}

    payload = {'merchant_request_id': merchant_id}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.exception('Error querying provider status for txn %s: %s', txn.pk, str(e))
        return {'status': 'unknown', 'error': str(e)}

    try:
        data = resp.json()
    except Exception:
        data = {'raw': resp.text}

    # Heuristic parsing
    # Accept explicit 0 as a valid success code. Use key-presence checks
    # because `0` is falsy and `or` would skip it.
    result_code = None
    if 'ResultCode' in data:
        result_code = data['ResultCode']
    elif 'result_code' in data:
        result_code = data['result_code']

    if result_code is not None:
        try:
            rc = int(result_code)
        except Exception:
            rc = None

        if rc == 0:
            return {'status': 'completed', 'result_code': 0, 'mpesa_receipt': data.get('MpesaReceiptNumber') or data.get('mpesa_receipt')}
        if rc is not None:
            return {'status': 'failed', 'result_code': rc}

    # Look for status field
    status = data.get('status') or data.get('transaction_status')
    if status:
        s = status.lower()
        if 'complete' in s or 'success' in s:
            return {'status': 'completed', 'mpesa_receipt': data.get('mpesa_receipt')}
        if 'fail' in s or 'cancel' in s:
            return {'status': 'failed'}

    return {'status': 'unknown', 'detail': data}


def reconcile_transaction_with_provider(txn: Transaction) -> bool:
    """Reconcile a single pending transaction against the provider. Returns True if changed."""
    if txn.status != 'pending':
        return False

    result = query_provider_status_for_txn(txn)
    status = result.get('status')
    if status == 'completed':
        # create a RawWebhook record representing provider's successful response
        # Normalize the provider response into the same shape as live callbacks
        payload = {
            'ResultCode': result.get('result_code', 0),
            'MerchantRequestID': txn.mpesa_code or '',
            'MpesaReceiptNumber': result.get('mpesa_receipt')
        }
        webhook = RawWebhook.objects.create(
            provider='megapay',
            provider_reference=txn.mpesa_code or '',
            payload=payload,
            headers={},
        )
        # process via existing helper
        return process_raw_webhook(webhook)
    elif status == 'failed':
        txn.status = 'failed'
        txn.completed_at = timezone.now()
        txn.save(update_fields=['status', 'completed_at'])
        return True

    return False
