from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='You must be 18 years or older to register.'
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'gender', 'orientation', 'date_of_birth', 'location')

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'bio', 'profile_picture', 'location', 'orientation')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('interests', 'height', 'occupation', 'education', 'relationship_goals', 'smoking_habits', 'drinking_habits', 'languages')
        widgets = {
            'interests': forms.Textarea(attrs={'rows': 3}),
        }