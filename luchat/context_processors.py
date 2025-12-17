from chat.models import Message

def global_unread_count(request):
    """Provide a global unread messages count for the current user."""
    if not request.user or not request.user.is_authenticated:
        return {'global_unread_count': 0}

    try:
        count = Message.objects.filter(room__participants=request.user, is_read=False).exclude(sender=request.user).count()
    except Exception:
        count = 0

    return {'global_unread_count': count}
