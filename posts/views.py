from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm
from matching.utils import MatchFinder
from django.template.loader import render_to_string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Post created successfully!')

            # Render the single-post partial for immediate AJAX response
            html = render_to_string('posts/_post_card.html', {
                'post': post,
                'user': request.user,
                'CHAT_COST': getattr(settings, 'CHAT_COST', 1),
            })

            # Broadcast to all connected clients via channel layer
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)('posts', {
                    'type': 'new.post',
                    'html': html,
                    'post_id': post.id,
                })
            except Exception:
                # non-fatal if channel layer isn't configured for async send
                pass

            # If client expects JSON (AJAX), return the rendered HTML
            accept = request.headers.get('Accept', '')
            if 'application/json' in accept or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'html': html, 'post_id': post.id})

            return redirect('dashboard')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    likes_count = post.likes.count()

    # Broadcast like update to connected clients
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('posts', {
            'type': 'post.like',
            'post_id': post.id,
            'likes_count': likes_count,
            'user': request.user.username,
            'liked': liked,
        })
    except Exception:
        pass

    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count
    })

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
        # Prepare comment payload
        comment_payload = {
            'id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%b %d, %Y %I:%M %p'),
            'profile_picture': comment.user.profile_picture.url if comment.user.profile_picture else '/media/profiles/default.png'
        }

        # Broadcast comment to clients
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)('posts', {
                'type': 'post.comment',
                'post_id': post.id,
                'comment': comment_payload,
            })
        except Exception:
            pass

        return JsonResponse({'success': True, 'comment': comment_payload})
    
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('dashboard')
    return render(request, 'posts/confirm_delete.html', {'post': post})