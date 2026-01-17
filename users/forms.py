from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile


# Predefined interest choices for better UX
INTEREST_CHOICES = [
    ('music', '🎵 Music'),
    ('travel', '✈️ Travel'),
    ('fitness', '💪 Fitness'),
    ('movies', '🎬 Movies'),
    ('food', '🍕 Food & Cooking'),
    ('gaming', '🎮 Gaming'),
    ('reading', '📚 Reading'),
    ('art', '🎨 Art & Design'),
    ('photography', '📷 Photography'),
    ('sports', '⚽ Sports'),
    ('nature', '🌿 Nature & Outdoors'),
    ('dancing', '💃 Dancing'),
    ('pets', '🐕 Pets & Animals'),
    ('technology', '💻 Technology'),
    ('fashion', '👗 Fashion'),
]

RELATIONSHIP_GOAL_CHOICES = [
    ('', 'Select what you\'re looking for...'),
    ('dating', '💕 Casual Dating'),
    ('relationship', '❤️ Serious Relationship'),
    ('friendship', '🤝 New Friends'),
    ('marriage', '💍 Marriage'),
    ('not_sure', '🤔 Not Sure Yet'),
]


class CustomUserCreationForm(UserCreationForm):
    """Enhanced registration form with profile fields for better matching."""
    
    email = forms.EmailField(required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='You must be 18 years or older to register.'
    )
    
    # Profile picture
    profile_picture = forms.ImageField(
        required=False,
        help_text='Upload a profile photo (recommended for better matches)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    # Bio
    bio = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tell others a bit about yourself... What makes you unique?'
        }),
        help_text='A short intro helps you stand out!'
    )
    
    # Interests (multiple choice)
    interests = forms.MultipleChoiceField(
        required=False,
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'interest-checkbox'}),
        help_text='Select your interests (helps find compatible matches)'
    )
    
    # Relationship goals
    relationship_goals = forms.ChoiceField(
        required=False,
        choices=RELATIONSHIP_GOAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='What are you looking for?'
    )
    
    # Occupation
    occupation = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Software Engineer, Teacher, Student...'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password1', 'password2',
            'gender', 'orientation', 'date_of_birth', 'location',
            'profile_picture', 'bio'
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set additional user fields
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
        if self.cleaned_data.get('bio'):
            user.bio = self.cleaned_data['bio']
        
        if commit:
            user.save()
            
            # Create or update UserProfile with additional fields
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Save interests as comma-separated string
            interests = self.cleaned_data.get('interests', [])
            if interests:
                # Convert choice keys to display names
                interest_names = []
                interest_dict = dict(INTEREST_CHOICES)
                for interest in interests:
                    if interest in interest_dict:
                        # Remove emoji for cleaner storage
                        name = interest_dict[interest].split(' ', 1)[-1] if ' ' in interest_dict[interest] else interest_dict[interest]
                        interest_names.append(name)
                profile.interests = ', '.join(interest_names)
            
            if self.cleaned_data.get('relationship_goals'):
                profile.relationship_goals = self.cleaned_data['relationship_goals']
            
            if self.cleaned_data.get('occupation'):
                profile.occupation = self.cleaned_data['occupation']
            
            profile.save()
        
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'bio', 'profile_picture', 'location', 'orientation')


class ProfileUpdateForm(forms.ModelForm):
    interests = forms.MultipleChoiceField(
        required=False,
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'interest-checkbox'}),
    )
    
    relationship_goals = forms.ChoiceField(
        required=False,
        choices=RELATIONSHIP_GOAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    
    class Meta:
        model = UserProfile
        fields = ('interests', 'height', 'occupation', 'education', 'relationship_goals', 'smoking_habits', 'drinking_habits', 'languages')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select current interests
        if self.instance and self.instance.interests:
            current_interests = [i.strip().lower() for i in self.instance.interests.split(',')]
            # Map back to choice keys
            selected = []
            for key, label in INTEREST_CHOICES:
                label_text = label.split(' ', 1)[-1].lower() if ' ' in label else label.lower()
                if label_text in current_interests or key in current_interests:
                    selected.append(key)
            self.initial['interests'] = selected
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Convert interests list to comma-separated string
        interests = self.cleaned_data.get('interests', [])
        if interests:
            interest_names = []
            interest_dict = dict(INTEREST_CHOICES)
            for interest in interests:
                if interest in interest_dict:
                    name = interest_dict[interest].split(' ', 1)[-1] if ' ' in interest_dict[interest] else interest_dict[interest]
                    interest_names.append(name)
            profile.interests = ', '.join(interest_names)
        else:
            profile.interests = ''
        
        if commit:
            profile.save()
        return profile