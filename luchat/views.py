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
from chat.models import Message
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta

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
    # Get compatible users for feed (exclude self) and build initial posts list
    compatible_users = MatchFinder.get_compatible_users(request.user)
    compatible_user_ids = list(compatible_users.exclude(id=request.user.id).values_list('id', flat=True))

    # Get posts from compatible users — include the current user's own posts so they see what they post
    from django.db.models import Q
    base_qs = Post.objects.select_related('user').prefetch_related('comments', 'likes', 'comments__user')
    posts = list(base_qs.filter(Q(user_id__in=compatible_user_ids) | Q(user=request.user)).order_by('-created_at')[:20])

    # If the result is small (or empty) fill the feed with recent global posts to ensure the feed isn't dominated
    # by only the viewer's posts. This helps new users and avoids the 'only my posts remain after refresh' issue.
    if len(posts) < 20:
        existing_ids = [p.id for p in posts]
        extra_qs = base_qs.exclude(id__in=existing_ids).order_by('-created_at')[:(20 - len(posts))]
        posts.extend(list(extra_qs))
    # mark whether the current user liked each post to avoid complex template logic
    for post in posts:
        post.is_liked = post.likes.filter(user=request.user).exists()
    
    # Provide "all online" list using recent activity window to avoid stale flags
    recent_threshold = timezone.now() - timedelta(minutes=5)
    base_all_online_qs = CustomUser.objects.filter(last_activity__gte=recent_threshold).exclude(id=request.user.id).order_by('-last_activity')
    all_online = base_all_online_qs[:12]

    # Compatible (opposite-gender only) fallback: prefer a simple opposite-gender filter
    if getattr(request.user, 'gender', None) in ('M', 'F'):
        opposite_gender = 'F' if request.user.gender == 'M' else 'M'
        online_users = base_all_online_qs.filter(gender=opposite_gender)[:12]
    else:
        # fallback to existing MatchFinder rules for other orientations
        online_users = MatchFinder.get_online_users(request.user)
    
    # Get suggested matches
    # Prefer a simple opposite-gender list on the dashboard for clarity
    if getattr(request.user, 'gender', None) in ('M', 'F'):
        opposite_gender = 'F' if request.user.gender == 'M' else 'M'
        suggested_matches = CustomUser.objects.filter(
            gender=opposite_gender,
            is_active=True
        ).order_by('-is_online', '-last_activity')[:5]
    else:
        suggested_matches = MatchFinder.get_suggested_matches(request.user, limit=5)
    
    context = {
        'posts': posts,
        'online_users': online_users,
        'suggested_matches': suggested_matches,
        'compatible_users': compatible_users[:10],
        'all_online': all_online,
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

    # Recent chats: include last message and unread count for dashboard preview
    recent_rooms = ChatRoom.objects.filter(participants=request.user, is_active=True).annotate(
        last_msg=Max('messages__timestamp')
    ).order_by('-last_msg')[:8]

    recent_chats = []
    for r in recent_rooms:
        other = r.participants.exclude(id=request.user.id).first()
        if not other:
            continue
        last_message = r.messages.order_by('-timestamp').first()
        unread_count = r.messages.filter(is_read=False).exclude(sender=request.user).count()
        preview = (last_message.content[:120] + '...') if last_message and len(last_message.content) > 120 else (last_message.content if last_message else '')
        recent_chats.append({
            'id': r.id,
            'other_user': other,
            'last_message': last_message,
            'unread_count': unread_count,
            'preview': preview,
        })

    context['recent_chats'] = recent_chats

    return render(request, 'dashboard.html', context)