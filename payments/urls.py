from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('buy-coins/', views.buy_coins, name='buy_coins'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    # Local MegaPay stub for development testing
    path('_megapay_stub/mpesa/stk-push', views.megapay_stub_stk_push, name='megapay_stub_stk_push'),
]