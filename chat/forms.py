from django import forms

class MessageForm(forms.Form):
    message = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type your message...',
            'autocomplete': 'off'
        })
    )