from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Post, Comment, Like
from .forms import PostForm, CommentForm
from matching.utils import MatchFinder

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
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
    
    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count()
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
        
        return JsonResponse({
            'success': True,
            'comment': {
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y %I:%M %p'),
                'profile_picture': comment.user.profile_picture.url if comment.user.profile_picture else '/media/profiles/default.png'
            }
        })
    
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('dashboard')
    return render(request, 'posts/confirm_delete.html', {'post': post})