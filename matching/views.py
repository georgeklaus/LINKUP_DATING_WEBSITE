from django.shortcuts import render, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .models import UserLike, UserDislike, Match
from .utils import MatchFinder
from users.models import CustomUser


@login_required
def discover(request):
    """
    Main discover view with support for:
    - Filter tabs (all, online, new, popular, compatible)
    - Advanced filters (age, gender, interests, goals)
    - AJAX pagination for infinite scroll
    """
    # Parse filters from request
    filters = {
        'filter_type': request.GET.get('filter', 'all'),
        'age_min': request.GET.get('age_min'),
        'age_max': request.GET.get('age_max'),
        'gender': request.GET.get('gender', 'all'),
        'interests': request.GET.getlist('interests'),
        'goals': request.GET.getlist('goals'),
        'verified_only': request.GET.get('verified_only') == 'true',
    }
    
    # Get page number
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    # Check if AJAX request
    is_ajax = request.GET.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get discover results using enhanced MatchFinder
    results = MatchFinder.get_discover_users(
        user=request.user,
        filters=filters,
        page=page,
        per_page=per_page
    )
    
    # Convert results to template-friendly format
    suggested_matches = []
    for item in results['users']:
        user_obj = item['user']
        # Attach computed properties to user object for template access
        user_obj.compatibility_score = item['compatibility_score']
        user_obj.computed_age = item['age']
        user_obj.is_new = item['is_new']
        user_obj.interests_list = item['interests_list']
        suggested_matches.append(user_obj)
    
    # Get online count for stats
    online_count = MatchFinder.get_online_users(request.user).count()
    
    # For AJAX requests, return JSON with rendered HTML
    if is_ajax:
        html = render_to_string(
            'matching/_match_cards.html',
            {
                'suggested_matches': suggested_matches,
                'user': request.user,
            },
            request=request
        )
        return JsonResponse({
            'success': True,
            'html': html,
            'has_more': results['has_more'],
            'total_count': results['total_count'],
            'page': page,
        })
    
    # Regular page render
    context = {
        'suggested_matches': suggested_matches,
        'online_count': online_count,
        'total_count': results['total_count'],
        'current_filter': filters['filter_type'],
        'filters': filters,
    }
    return render(request, 'matching/discover.html', context)


@login_required
@require_GET
def discover_filter(request):
    """
    AJAX endpoint for applying advanced filters.
    Returns filtered users as JSON with rendered HTML cards.
    """
    # Parse all filter parameters
    filters = {
        'filter_type': request.GET.get('filter', 'all'),
        'age_min': request.GET.get('age_min'),
        'age_max': request.GET.get('age_max'),
        'gender': request.GET.get('gender', 'all'),
        'interests': request.GET.getlist('interests'),
        'goals': request.GET.getlist('goals'),
        'verified_only': request.GET.get('verified_only') == 'true',
    }
    
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    # Get filtered results
    results = MatchFinder.get_discover_users(
        user=request.user,
        filters=filters,
        page=page,
        per_page=per_page
    )
    
    # Prepare users for template
    suggested_matches = []
    for item in results['users']:
        user_obj = item['user']
        user_obj.compatibility_score = item['compatibility_score']
        user_obj.computed_age = item['age']
        user_obj.is_new = item['is_new']
        user_obj.interests_list = item['interests_list']
        suggested_matches.append(user_obj)
    
    # Render cards HTML
    html = render_to_string(
        'matching/_match_cards.html',
        {
            'suggested_matches': suggested_matches,
            'user': request.user,
        },
        request=request
    )
    
    return JsonResponse({
        'success': True,
        'html': html,
        'has_more': results['has_more'],
        'total_count': results['total_count'],
        'page': page,
        'online_count': MatchFinder.get_online_users(request.user).count(),
    })

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
@require_POST
def superlike_user(request, username):
    """Mark a user as superliked. Similar to like but flagged differently."""
    target = get_object_or_404(CustomUser, username=username)

    # Create like record if not exists
    like, created = UserLike.objects.get_or_create(
        user=request.user,
        liked_user=target
    )

    # Flag as superlike (store in UserLike if model has field, otherwise create entry in UserDislike as placeholder)
    try:
        # if UserLike has `is_superlike` field
        if hasattr(like, 'is_superlike'):
            like.is_superlike = True
            like.save()
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'message': f'You superliked {target.username}'
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