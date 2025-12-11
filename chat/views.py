from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import ChatRoom, Message, VideoCall
from users.models import CustomUser
from matching.utils import MatchFinder
from django.conf import settings
import uuid

@login_required
def chat_list(request):
    # Get all chat rooms where user is a participant
    chat_rooms = ChatRoom.objects.filter(participants=request.user, is_active=True)
    
    # Get last message for each room
    rooms_with_last_message = []
    for room in chat_rooms:
        last_message = room.messages.last()
        other_participant = room.participants.exclude(id=request.user.id).first()
        
        rooms_with_last_message.append({
            'room': room,
            'last_message': last_message,
            'other_participant': other_participant,
            'unread_count': room.messages.filter(is_read=False).exclude(sender=request.user).count()
        })
    
    context = {
        'chat_rooms': rooms_with_last_message,
    }
    return render(request, 'chat/chat_list.html', context)

@login_required
def chat_room(request, username):
    other_user = get_object_or_404(CustomUser, username=username)
    
    # Check if users can chat (compatible)
    compatible_users = MatchFinder.get_compatible_users(request.user)
    if other_user not in compatible_users:
        messages.error(request, "You cannot chat with this user")
        return redirect('dashboard')
    
    # Get or create chat room
    room_name = get_chat_room_name(request.user, other_user)
    chat_room, created = ChatRoom.objects.get_or_create(name=room_name)
    
    if created:
        chat_room.participants.add(request.user, other_user)
    
    messages = chat_room.messages.all().order_by('timestamp')[:50]
    
    # Mark messages as read
    chat_room.messages.filter(sender=other_user, is_read=False).update(is_read=True)
    
    context = {
        'room_name': room_name,
        'other_user': other_user,
        'messages': messages,
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def start_video_call(request, username):
    other_user = get_object_or_404(CustomUser, username=username)
    
    # Check if user has enough coins for at least 1 minute
    if request.user.coins < settings.VIDEO_CALL_COST_PER_MIN:
        return JsonResponse({'success': False, 'error': 'Insufficient coins'})
    
    # Create video call room
    room_name = f"video_call_{uuid.uuid4().hex}"
    video_call = VideoCall.objects.create(
        caller=request.user,
        receiver=other_user,
        room_name=room_name,
        is_active=True
    )
    
    return JsonResponse({
        'success': True,
        'room_name': room_name,
        'call_id': video_call.id
    })

def get_chat_room_name(user1, user2):
    """Generate unique room name for two users"""
    user_ids = sorted([user1.id, user2.id])
    return f"chat_{user_ids[0]}_{user_ids[1]}"