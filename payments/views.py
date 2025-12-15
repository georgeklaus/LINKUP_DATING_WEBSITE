import requests
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages

logger = logging.getLogger(__name__)
from .models import CoinPackage, Transaction
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

            if not megapay_key or not megapay_base:
                messages.error(request, 'Payment provider is not configured. Please contact the site administrator.')
                context = {'packages': packages}
                return render(request, 'payments/buy_coins.html', context)

            headers = {
                'Authorization': f'Bearer {megapay_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'phone_number': phone_number,
                'amount': package.amount,
                'transaction_reference': f"COINS_{request.user.id}_{package.id}",
                'callback_url': f"{request.build_absolute_uri('/')}payments/mpesa-callback/"
            }
            
            try:
                request_url = f"{megapay_base}/mpesa/stk-push"
                # Log the outgoing request for debugging (avoid logging sensitive keys in production)
                logger.debug('MegaPay request URL: %s', request_url)
                logger.debug('MegaPay request headers: %s', {k: ('<redacted>' if 'Authorization' in k else v) for k,v in headers.items()})
                logger.debug('MegaPay request payload: %s', payload)

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
                    except Exception:
                        resp_json = {}

                    merchant_id = resp_json.get('merchant_request_id') or resp_json.get('MerchantRequestID') or resp_json.get('merchantRequestId') or resp_json.get('merchant_request')

                    # Create transaction record and attach provider id when available
                    transaction = Transaction.objects.create(
                        user=request.user,
                        package=package,
                        phone_number=phone_number,
                        amount=package.amount,
                        coins=package.coins,
                        status='pending',
                        mpesa_code=(merchant_id or f"COINS_{request.user.id}_{package.id}")
                    )

                    messages.success(request, 'Payment initiated successfully! Check your phone to complete the transaction.')
                    return redirect('payments:payment_success')
                else:
                    # Log response for debugging
                    try:
                        body = response.text
                    except Exception:
                        body = '<unavailable>'
                    logger.error('MegaPay initiation failed: status=%s body=%s', response.status_code, body)
                    messages.error(request, 'Failed to initiate payment (provider error). Please try again later.')
                    
            except requests.exceptions.RequestException as e:
                logger.exception('MegaPay request exception')
                messages.error(request, f'Payment service temporarily unavailable. Error: {str(e)}')
                
        except CoinPackage.DoesNotExist:
            messages.error(request, 'Invalid coin package selected.')
    
    context = {
        'packages': packages,
    }
    return render(request, 'payments/buy_coins.html', context)

@login_required
def payment_success(request):
    return render(request, 'payments/payment_success.html')

@login_required
def payment_failed(request):
    return render(request, 'payments/payment_failed.html')

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Process M-Pesa callback
            result_code = data.get('ResultCode')
            merchant_request_id = data.get('MerchantRequestID')
            mpesa_receipt_number = data.get('MpesaReceiptNumber')
            
            if result_code == 0:
                # Payment successful
                try:
                    transaction = Transaction.objects.get(
                        mpesa_code=merchant_request_id,
                        status='pending'
                    )
                    transaction.status = 'completed'
                    transaction.mpesa_code = mpesa_receipt_number
                    transaction.completed_at = timezone.now()
                    transaction.save()
                    
                    # Add coins to user
                    transaction.user.add_coins(transaction.coins)
                    
                except Transaction.DoesNotExist:
                    pass
            
            return JsonResponse({'status': 'ok'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


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

    # Simulate successful initiation and trigger callback to our server
    merchant_req = f"stub_{uuid.uuid4().hex}"

    # Attempt to POST back to callback_url to simulate provider callback
    callback_payload = {
        'ResultCode': 0,
        'MerchantRequestID': merchant_req,
        'MpesaReceiptNumber': f'STUB{uuid.uuid4().hex[:8]}'
    }

    try:
        # best-effort; if callback_url is local it should be reachable
        requests.post(data['callback_url'], json=callback_payload, timeout=5)
    except Exception:
        logger.exception('Failed to POST simulated callback to %s', data.get('callback_url'))

    response = {
        'status': 'success',
        'message': 'STK Push initiated (stub)',
        'merchant_request_id': merchant_req,
    }

    return JsonResponse(response)