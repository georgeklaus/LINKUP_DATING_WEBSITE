from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UserLike, UserDislike, Match
from .utils import MatchFinder
from users.models import CustomUser

@login_required
def discover(request):
    # Build an ordered queryset first, exclude liked/disliked users, then slice
    online_users = MatchFinder.get_online_users(request.user)

    # Exclude users already liked or disliked
    liked_users = UserLike.objects.filter(user=request.user).values_list('liked_user_id', flat=True)
    disliked_users = UserDislike.objects.filter(user=request.user).values_list('disliked_user_id', flat=True)

    suggested_qs = MatchFinder.get_compatible_users(request.user).order_by('-is_online', '-last_activity')
    suggested_qs = suggested_qs.exclude(id__in=list(liked_users) + list(disliked_users))
    suggested_matches = suggested_qs[:20]
    
    context = {
        'suggested_matches': suggested_matches,
        'online_users': online_users,
    }
    return render(request, 'matching/discover.html', context)

@login_required
@require_POST
def like_user(request, username):
    liked_user = get_object_or_404(CustomUser, username=username)
    
    # Check if users can interact (compatible)
    if not MatchFinder.can_view_profile(request.user, liked_user):
        return JsonResponse({'success': False, 'error': 'Cannot like this user'})
    
    # Create like
    like, created = UserLike.objects.get_or_create(
        user=request.user,
        liked_user=liked_user
    )
    
    # Check for mutual like (match)
    mutual_like = UserLike.objects.filter(
        user=liked_user,
        liked_user=request.user
    ).exists()
    
    if mutual_like and created:
        # Create match
        match = Match.objects.create(
            user1=request.user,
            user2=liked_user
        )
        return JsonResponse({
            'success': True, 
            'matched': True,
            'message': f'It\'s a match! You and {liked_user.username} like each other.'
        })
    
    return JsonResponse({
        'success': True, 
        'matched': False,
        'message': f'You liked {liked_user.username}'
    })

@login_required
@require_POST
def dislike_user(request, username):
    disliked_user = get_object_or_404(CustomUser, username=username)
    
    # Create dislike
    dislike, created = UserDislike.objects.get_or_create(
        user=request.user,
        disliked_user=disliked_user
    )
    
    return JsonResponse({
        'success': True,
        'message': f'You passed on {disliked_user.username}'
    })

@login_required
def matches_list(request):
    # Get user's matches
    matches = Match.objects.filter(
        (models.Q(user1=request.user) | models.Q(user2=request.user)) &
        models.Q(is_active=True)
    ).select_related('user1', 'user2')
    
    match_data = []
    for match in matches:
        other_user = match.user2 if match.user1 == request.user else match.user1
        match_data.append({
            'match': match,
            'other_user': other_user
        })
    
    context = {
        'matches': match_data
    }
    return render(request, 'matching/matches_list.html', context)