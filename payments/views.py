import requests
import json
import logging
import uuid
import hmac
import hashlib
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)
from .models import CoinPackage, Transaction
from .models import RawWebhook
from users.models import CustomUser

@login_required
def buy_coins(request):
    packages = CoinPackage.objects.filter(is_active=True)
    
    if request.method == 'POST':
        package_id = request.POST.get('package')
        phone_number = request.POST.get('phone_number')
        
        try:
            package = CoinPackage.objects.get(id=package_id, is_active=True)
            
            # MegaPay M-Pesa integration
            megapay_key = getattr(settings, 'MEGAPAY_API_KEY', None)
            megapay_base = getattr(settings, 'MEGAPAY_BASE_URL', None)
            megapay_email = getattr(settings, 'MEGAPAY_EMAIL', None)

            if not megapay_key or not megapay_base or not megapay_email:
                messages.error(request, 'Payment provider is not configured. Please contact the site administrator.')
                context = {'packages': packages}
                return render(request, 'payments/buy_coins.html', context)

            headers = {
                'Content-Type': 'application/json'
            }

            # Use a unique transaction reference per initiation to avoid duplicates
            unique_suffix = uuid.uuid4().hex[:8]
            provisional_ref = f"COINS_{request.user.id}_{package.id}_{unique_suffix}"

            # MegaPay API format - api_key and email go in the body, not header
            payload = {
                'api_key': megapay_key,
                'email': megapay_email,
                'amount': str(package.amount),
                'msisdn': phone_number,
                'reference': provisional_ref
            }

            # Create a pending transaction before calling the provider to avoid
            # race conditions where provider callbacks arrive before we persist the txn.
            transaction = Transaction.objects.create(
                user=request.user,
                package=package,
                phone_number=phone_number,
                amount=package.amount,
                coins=package.coins,
                status='pending',
                mpesa_code=provisional_ref
            )

            try:
                request_url = f"{megapay_base}/initiatestk"
                # Log the outgoing request for debugging (avoid logging sensitive keys in production)
                logger.debug('MegaPay request URL: %s', request_url)
                logger.debug('MegaPay request payload: %s', {k: ('<redacted>' if k == 'api_key' else v) for k,v in payload.items()})

                response = requests.post(
                    request_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Parse provider response for merchant/request id if present
                    try:
                        resp_json = response.json()
                        logger.info('MegaPay response: %s', resp_json)
                    except Exception:
                        resp_json = {}

                    # MegaPay returns transaction_request_id on success
                    # BUT - webhook comes back with our original reference, so don't overwrite mpesa_code
                    # Just log the MegaPay transaction ID for reference
                    transaction_request_id = resp_json.get('transaction_request_id') or resp_json.get('TransactionID')
                    if transaction_request_id:
                        logger.info('MegaPay TransactionID: %s for our ref: %s', transaction_request_id, provisional_ref)

                    messages.success(request, 'Payment initiated! Check your phone for the M-Pesa prompt and enter your PIN.')
                    # Always redirect to pending page - payment isn't complete until webhook confirms it
                    return redirect('payments:pending_payment', txn_id=transaction.id)
                else:
                    # Log response for debugging
                    try:
                        body = response.text
                    except Exception:
                        body = '<unavailable>'
                    logger.error('MegaPay initiation failed: status=%s body=%s', response.status_code, body)
                    # mark txn failed for visibility
                    try:
                        transaction.status = 'failed'
                        transaction.save(update_fields=['status'])
                    except Exception:
                        logger.exception('Failed to mark transaction failed')
                    messages.error(request, 'Failed to initiate payment (provider error). Please try again later.')
                    
            except requests.exceptions.RequestException as e:
                logger.exception('MegaPay request exception')
                try:
                    transaction.status = 'failed'
                    transaction.save(update_fields=['status'])
                except Exception:
                    logger.exception('Failed to mark transaction failed after exception')
                messages.error(request, f'Payment service temporarily unavailable. Error: {str(e)}')
                
        except CoinPackage.DoesNotExist:
            messages.error(request, 'Invalid coin package selected.')
    
    context = {
        'packages': packages,
    }
    return render(request, 'payments/buy_coins.html', context)

@login_required
def payment_success(request):
    return render(request, 'payments/payment_successful.html')

@login_required
def payment_failed(request):
    return render(request, 'payments/payment_failed.html')

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            # Persist raw payload immediately for audit/debug
            raw_body = request.body
            try:
                data = json.loads(raw_body)
            except json.JSONDecodeError:
                data = {}

            # Grab common provider reference keys
            merchant_request_id = data.get('MerchantRequestID') or data.get('merchant_request_id') or data.get('MerchantRequestId') or ''

            # Collect headers (only HTTP_ headers to avoid storing wsgi internals)
            headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}

            webhook = RawWebhook.objects.create(
                provider='megapay',
                provider_reference=merchant_request_id or '',
                payload=data or {},
                headers=headers,
            )
            logger.info('Created RawWebhook id=%s provider_ref=%s', getattr(webhook, 'id', None), getattr(webhook, 'provider_reference', None))

            # Verification: optional HMAC signature and IP allowlist
            secret = getattr(settings, 'MEGAPAY_WEBHOOK_SECRET', None)
            enforce_sig = getattr(settings, 'MEGAPAY_ENFORCE_WEBHOOK_SIGNATURE', False)
            signature_header = (request.META.get('HTTP_X_MEGAPAY_SIGNATURE') or
                                request.META.get('HTTP_X_SIGNATURE') or
                                request.META.get('HTTP_X_HUB_SIGNATURE'))
            remote_addr = request.META.get('REMOTE_ADDR')
            allowed_ips = getattr(settings, 'MEGAPAY_CALLBACK_ALLOWED_IPS', None)

            if allowed_ips:
                if remote_addr not in allowed_ips:
                    logger.warning('Callback from disallowed IP %s', remote_addr)
                    return JsonResponse({'status': 'forbidden'}, status=403)

            # If a secret is configured, expect a signature header (optional enforcement)
            if secret:
                if not signature_header:
                    if enforce_sig:
                        logger.warning('Missing webhook signature for provider ref %s', merchant_request_id)
                        return JsonResponse({'status': 'forbidden'}, status=403)
                    else:
                        logger.info('Webhook signature missing but not enforced (dev mode)')
                else:
                    # Accept formats like 'sha256=<hex>' or raw hex
                    sig = signature_header
                    if sig.startswith('sha256='):
                        sig = sig.split('=', 1)[1]
                    try:
                        computed = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
                        if not hmac.compare_digest(computed, sig):
                            logger.warning('Webhook signature mismatch for provider ref %s', merchant_request_id)
                            return JsonResponse({'status': 'forbidden'}, status=403)
                    except Exception:
                        logger.exception('Error verifying webhook signature')
                        return JsonResponse({'status': 'forbidden'}, status=403)

            # Hand off processing to the shared helper so admin and callbacks behave identically
            try:
                from . import utils as payments_utils
                payments_utils.process_raw_webhook(webhook)
            except Exception:
                logger.exception('Failed to process webhook %s via helper', webhook.pk)

            return JsonResponse({'status': 'ok'})

        except Exception:
            logger.exception('Unexpected error in mpesa_callback')
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@login_required
def pending_payment(request, txn_id):
    txn = get_object_or_404(Transaction, pk=txn_id, user=request.user)
    
    # Support AJAX polling for status updates
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': txn.status,
            'coins': txn.coins,
            'amount': txn.amount,
        })
    
    return render(request, 'payments/pending_payment.html', {'transaction': txn})


@csrf_exempt
def megapay_stub_trigger(request):
    """Manual trigger for the dev stub. Accepts POST with 'transaction_reference' or 'txn_id'
    and posts a simulated callback to the site's mpesa callback endpoint."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    txn = None
    txn_ref = data.get('transaction_reference')
    txn_id = data.get('txn_id')
    if txn_id:
        try:
            txn = Transaction.objects.get(pk=int(txn_id))
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    elif txn_ref:
        try:
            txn = Transaction.objects.get(mpesa_code=txn_ref)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'txn_id or transaction_reference required'}, status=400)

    # Build callback payload
    merchant_req = txn.mpesa_code or f"stub_{uuid.uuid4().hex}"
    callback_payload = {
        'ResultCode': 0,
        'MerchantRequestID': merchant_req,
        'MpesaReceiptNumber': f'STUB{uuid.uuid4().hex[:8]}'
    }

    # POST to our mpesa callback endpoint
    try:
        callback_url = request.build_absolute_uri('/payments/mpesa-callback/')
        requests.post(callback_url, json=callback_payload, timeout=5)
    except Exception:
        logger.exception('Failed to POST simulated callback to %s', callback_url)
        return JsonResponse({'status': 'error', 'message': 'failed to post callback'}, status=500)

    return JsonResponse({'status': 'ok', 'merchant_request_id': merchant_req})


@csrf_exempt
def megapay_stub_stk_push(request):
    """A simple development stub that mimics a MegaPay /mpesa/stk-push endpoint.

    It accepts POST JSON with phone_number, amount, transaction_reference, callback_url
    and returns a 200 JSON response that indicates initiation succeeded. The real
    flow would trigger a callback to `callback_url` later; for local tests you can
    trigger `mpesa_callback` manually or extend this stub to POST the callback.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    # Basic validation
    required = {'phone_number', 'amount', 'transaction_reference', 'callback_url'}
    if not required.issubset(set(data.keys())):
        return JsonResponse({'status': 'error', 'message': 'Missing fields'}, status=400)

    # Simulate successful initiation. Use the supplied transaction_reference
    # as the MerchantRequestID so local callbacks match the stored transaction.
    merchant_req = data.get('transaction_reference') or f"stub_{uuid.uuid4().hex}"

    # Attempt to POST back to callback_url to simulate provider callback
    callback_payload = {
        'ResultCode': 0,
        'MerchantRequestID': merchant_req,
        'MpesaReceiptNumber': f'STUB{uuid.uuid4().hex[:8]}'
    }

    # Only auto-post callback when explicitly enabled in settings. In
    # development we prefer manual simulation so the user can be prompted
    # for a PIN (pending page) before the callback completes the txn.
    auto_cb = getattr(settings, 'MEGAPAY_STUB_AUTO_CALLBACK', False)
    if auto_cb:
        try:
            # best-effort; if callback_url is local it should be reachable
            requests.post(data['callback_url'], json=callback_payload, timeout=5)
        except Exception:
            logger.exception('Failed to POST simulated callback to %s', data.get('callback_url'))
    else:
        logger.info('MegaPay stub auto-callback disabled for merchant_req=%s', merchant_req)

    response = {
        'status': 'success',
        'message': 'STK Push initiated (stub)',
        'merchant_request_id': merchant_req,
    }

    return JsonResponse(response)


@csrf_exempt
def megapay_stub_transaction_status(request):
    """Dev stub endpoint to respond to transaction-status queries from reconcile task.

    Expects POST JSON with `merchant_request_id` and returns a JSON containing
    `ResultCode` (0 for completed) and `MpesaReceiptNumber` when a matching
    pending Transaction exists. This is a development-only helper.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    merchant_req = data.get('merchant_request_id') or data.get('MerchantRequestID') or ''
    if not merchant_req:
        return JsonResponse({'status': 'error', 'message': 'merchant_request_id required'}, status=400)

    # If there's a pending transaction with this merchant_request_id, pretend it's completed.
    try:
        txn = Transaction.objects.filter(mpesa_code=merchant_req, status='pending').first()
    except Exception:
        txn = None

    if txn:
        return JsonResponse({
            'ResultCode': 0,
            'MerchantRequestID': merchant_req,
            'MpesaReceiptNumber': f'STUB{uuid.uuid4().hex[:8]}'
        })

    # Otherwise return not found/unknown status
    return JsonResponse({'status': 'not_found', 'detail': 'no pending txn for merchant_request_id'}, status=404)