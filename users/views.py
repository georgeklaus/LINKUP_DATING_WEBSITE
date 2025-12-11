from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser, UserProfile
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
from payments.models import ProfileView
from matching.utils import MatchFinder
from django.conf import settings

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request, username):
    user_to_view = get_object_or_404(CustomUser, username=username)
    
    if user_to_view == request.user:
        return redirect('users:settings')
    
    # Check if user can view this profile (matching logic)
    if not MatchFinder.can_view_profile(request.user, user_to_view):
        messages.error(request, "You cannot view this profile due to compatibility settings.")
        return redirect('dashboard')
    
    # Charge for profile view if not viewed recently
    if not ProfileView.objects.filter(
        viewer=request.user, 
        viewed_user=user_to_view,
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).exists():
        
        if request.user.deduct_coins(settings.PROFILE_VIEW_COST):
            ProfileView.objects.create(
                viewer=request.user,
                viewed_user=user_to_view,
                cost=settings.PROFILE_VIEW_COST
            )
        else:
            messages.error(request, "Not enough coins to view profile")
            return redirect('dashboard')
    
    context = {
        'profile_user': user_to_view,
    }
    return render(request, 'users/profile.html', context)

@login_required
def settings_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile_obj)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('users:settings')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_form = ProfileUpdateForm(instance=profile_obj)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/settings.html', context)

@login_required
def user_search(request):
    query = request.GET.get('q', '')
    users = CustomUser.objects.filter(
        Q(username__icontains=query) |
        Q(bio__icontains=query) |
        Q(location__icontains=query)
    ).exclude(id=request.user.id)
    
    # Filter by compatibility
    compatible_users = MatchFinder.get_compatible_users(request.user)
    users = users.filter(id__in=compatible_users.values_list('id', flat=True))
    
    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'users/search.html', context)