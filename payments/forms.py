from django import forms
from .models import CoinPackage

class PaymentForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2547XXXXXXXX',
            'pattern': '^2547\d{8}$'
        }),
        help_text='Enter your M-Pesa number in format 2547XXXXXXXX'
    )
    package = forms.ModelChoiceField(
        queryset=CoinPackage.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        empty_label=None
    )