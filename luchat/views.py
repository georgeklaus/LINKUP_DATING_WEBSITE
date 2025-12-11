from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from posts.models import Post
from matching.utils import MatchFinder
from users.forms import CustomUserCreationForm
from django.contrib.auth import login

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
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
def dashboard(request):
    # Get compatible users for feed
    compatible_users = MatchFinder.get_compatible_users(request.user)
    compatible_user_ids = compatible_users.values_list('id', flat=True)
    
    # Get posts from compatible users
    posts = Post.objects.filter(user_id__in=compatible_user_ids).select_related(
        'user'
    ).prefetch_related('comments', 'likes', 'comments__user')[:20]
    # mark whether the current user liked each post to avoid complex template logic
    for post in posts:
        post.is_liked = post.likes.filter(user=request.user).exists()
    
    # Get online users
    online_users = MatchFinder.get_online_users(request.user)
    
    # Get suggested matches
    suggested_matches = MatchFinder.get_suggested_matches(request.user, limit=5)
    
    context = {
        'posts': posts,
        'online_users': online_users,
        'suggested_matches': suggested_matches,
        'compatible_users': compatible_users[:10],
    }
    return render(request, 'dashboard.html', context)