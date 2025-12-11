import requests
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
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
            headers = {
                'Authorization': f'Bearer {settings.MEGAPAY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'phone_number': phone_number,
                'amount': package.amount,
                'transaction_reference': f"COINS_{request.user.id}_{package.id}",
                'callback_url': f"{request.build_absolute_uri('/')}payments/mpesa-callback/"
            }
            
            try:
                response = requests.post(
                    f"{settings.MEGAPAY_BASE_URL}/mpesa/stk-push",
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Create transaction record
                    transaction = Transaction.objects.create(
                        user=request.user,
                        package=package,
                        phone_number=phone_number,
                        amount=package.amount,
                        coins=package.coins,
                        status='pending'
                    )
                    
                    messages.success(request, 'Payment initiated successfully! Check your phone to complete the transaction.')
                    return redirect('payments:payment_success')
                else:
                    messages.error(request, 'Failed to initiate payment. Please try again.')
                    
            except requests.exceptions.RequestException as e:
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