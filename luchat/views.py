from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from posts.models import Post
from matching.utils import MatchFinder
from users.forms import CustomUserCreationForm
from django.contrib.auth import login
from chat.models import ChatRoom
from django.db.models import Max
from django.urls import reverse

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

    # Determine where 'My Messages' should go: default to chat list, but
    # if the user has a recent chat room, link directly to that room.
    last_room = ChatRoom.objects.filter(participants=request.user).annotate(
        last_msg=Max('messages__timestamp')
    ).order_by('-last_msg').first()

    if last_room:
        other = last_room.participants.exclude(id=request.user.id).first()
        if other:
            context['my_messages_link'] = reverse('chat:chat_room', args=[other.username])
        else:
            context['my_messages_link'] = reverse('chat:chat_list')
    else:
        context['my_messages_link'] = reverse('chat:chat_list')

    return render(request, 'dashboard.html', context)