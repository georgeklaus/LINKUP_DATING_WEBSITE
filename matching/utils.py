from django.db.models import Q, Count, F, Value, IntegerField, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser


class MatchFinder:
    # Constants for compatibility scoring
    INTEREST_MATCH_WEIGHT = 15
    ORIENTATION_MATCH_WEIGHT = 20
    ONLINE_BONUS = 10
    NEW_USER_BONUS = 5
    LOCATION_MATCH_WEIGHT = 10
    
    @staticmethod
    def get_compatible_users(user):
        """Return queryset of compatible users based on gender and orientation"""
        compatible_genders = MatchFinder.get_compatible_genders(
            user.gender, 
            user.orientation
        )
        
        return CustomUser.objects.filter(
            gender__in=compatible_genders,
            orientation=user.orientation,
            is_active=True
        ).exclude(id=user.id).select_related('profile')
    
    @staticmethod
    def get_compatible_genders(gender, orientation):
        """Define compatibility rules"""
        rules = {
            # Male straight sees Female straight
            ('M', 'straight'): ['F'],
            # Female straight sees Male straight  
            ('F', 'straight'): ['M'],
            # Male gay sees Male gay
            ('M', 'gay'): ['M'],
            # Female lesbian sees Female lesbian
            ('F', 'lesbian'): ['F'],
            # Bisexual sees both genders with same orientation
            ('M', 'bisexual'): ['M', 'F'],
            ('F', 'bisexual'): ['M', 'F'],
        }
        
        return rules.get((gender, orientation), [])
    
    @staticmethod
    def get_online_users(user):
        """Get online compatible users"""
        compatible_users = MatchFinder.get_compatible_users(user)
        return compatible_users.filter(is_online=True)
    
    @staticmethod
    def can_view_profile(viewer, viewed_user):
        """Check if viewer can view the profile based on gender and orientation"""
        compatible_users = MatchFinder.get_compatible_users(viewer)
        return viewed_user in compatible_users
    
    @staticmethod
    def get_suggested_matches(user, limit=10):
        """Get suggested matches for user"""
        compatible_users = MatchFinder.get_compatible_users(user)
        return compatible_users.order_by('-is_online', '-last_activity')[:limit]
    
    @staticmethod
    def calculate_compatibility_score(user, target_user):
        """
        Calculate compatibility score between two users (0-100%).
        Based on: shared interests, location, orientation match, activity.
        """
        score = 50  # Base score
        
        # Get user interests
        try:
            user_interests = set(
                i.strip().lower() 
                for i in (user.profile.interests or '').split(',') 
                if i.strip()
            )
            target_interests = set(
                i.strip().lower() 
                for i in (target_user.profile.interests or '').split(',') 
                if i.strip()
            )
            
            # Calculate interest overlap
            if user_interests and target_interests:
                overlap = len(user_interests & target_interests)
                total = len(user_interests | target_interests)
                if total > 0:
                    interest_score = (overlap / total) * MatchFinder.INTEREST_MATCH_WEIGHT
                    score += interest_score
        except Exception:
            pass
        
        # Location bonus (same location)
        if user.location and target_user.location:
            if user.location.lower() == target_user.location.lower():
                score += MatchFinder.LOCATION_MATCH_WEIGHT
        
        # Online bonus
        if target_user.is_online:
            score += MatchFinder.ONLINE_BONUS
        
        # New user bonus (joined within 7 days)
        if MatchFinder.is_new_user(target_user):
            score += MatchFinder.NEW_USER_BONUS
        
        # Cap at 100
        return min(100, max(0, int(score)))
    
    @staticmethod
    def is_new_user(user, days=7):
        """Check if user joined within the last N days"""
        cutoff = timezone.now() - timedelta(days=days)
        return user.date_joined >= cutoff
    
    @staticmethod
    def get_user_age(user):
        """Get user age from date_of_birth"""
        if user.date_of_birth:
            today = timezone.now().date()
            return today.year - user.date_of_birth.year - (
                (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
            )
        return None
    
    @staticmethod
    def get_filtered_users(user, filters=None, exclude_ids=None):
        """
        Get filtered compatible users based on advanced filters.
        
        Filters dict can contain:
        - filter_type: 'all', 'online', 'new', 'popular', 'compatible'
        - age_min: minimum age
        - age_max: maximum age
        - gender: 'all', 'male', 'female', 'other'
        - interests: list of interest keywords
        - goals: list of relationship goals
        - verified_only: boolean
        """
        filters = filters or {}
        exclude_ids = exclude_ids or []
        
        # Start with compatible users
        queryset = MatchFinder.get_compatible_users(user)
        
        # Exclude already interacted users
        if exclude_ids:
            queryset = queryset.exclude(id__in=exclude_ids)
        
        # Apply filter type
        filter_type = filters.get('filter_type', 'all')
        
        if filter_type == 'online':
            queryset = queryset.filter(is_online=True)
        
        elif filter_type == 'new':
            # Users who joined in last 7 days
            cutoff = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(date_joined__gte=cutoff)
        
        elif filter_type == 'popular':
            # Sort by likes received (most liked first)
            queryset = queryset.annotate(
                likes_count=Count('likes_received')
            ).order_by('-likes_count', '-is_online')
        
        elif filter_type == 'compatible':
            # Will be sorted by compatibility score later
            pass
        
        # Age filter
        age_min = filters.get('age_min')
        age_max = filters.get('age_max')
        
        if age_min or age_max:
            today = timezone.now().date()
            
            if age_max:
                # Born at least age_max years ago
                min_birth = today.replace(year=today.year - int(age_max) - 1)
                queryset = queryset.filter(date_of_birth__gte=min_birth)
            
            if age_min:
                # Born at most age_min years ago
                max_birth = today.replace(year=today.year - int(age_min))
                queryset = queryset.filter(date_of_birth__lte=max_birth)
        
        # Gender filter (override orientation-based if specified)
        gender_filter = filters.get('gender')
        if gender_filter and gender_filter != 'all':
            gender_map = {'male': 'M', 'female': 'F'}
            if gender_filter in gender_map:
                queryset = queryset.filter(gender=gender_map[gender_filter])
        
        # Interests filter
        interests = filters.get('interests', [])
        if interests:
            interest_q = Q()
            for interest in interests:
                interest_q |= Q(profile__interests__icontains=interest)
            queryset = queryset.filter(interest_q)
        
        # Relationship goals filter
        goals = filters.get('goals', [])
        if goals:
            goals_q = Q()
            for goal in goals:
                goals_q |= Q(profile__relationship_goals__icontains=goal)
            queryset = queryset.filter(goals_q)
        
        # Default ordering
        if filter_type not in ['popular']:
            queryset = queryset.order_by('-is_online', '-last_activity')
        
        return queryset
    
    @staticmethod
    def annotate_with_scores(user, queryset):
        """
        Annotate queryset with compatibility scores and other metadata.
        Returns list of dicts with user and computed fields.
        """
        results = []
        for target_user in queryset:
            score = MatchFinder.calculate_compatibility_score(user, target_user)
            age = MatchFinder.get_user_age(target_user)
            is_new = MatchFinder.is_new_user(target_user)
            
            # Get interests as list
            interests_list = []
            try:
                if target_user.profile and target_user.profile.interests:
                    interests_list = [
                        i.strip() for i in target_user.profile.interests.split(',')
                        if i.strip()
                    ][:5]  # Limit to 5
            except Exception:
                pass
            
            results.append({
                'user': target_user,
                'compatibility_score': score,
                'age': age,
                'is_new': is_new,
                'interests_list': interests_list,
            })
        
        return results
    
    @staticmethod
    def get_discover_users(user, filters=None, exclude_ids=None, page=1, per_page=20):
        """
        Main method for discover page - returns paginated, filtered, scored users.
        """
        from matching.models import UserLike, UserDislike
        
        # Get users already liked/disliked
        liked_ids = list(UserLike.objects.filter(user=user).values_list('liked_user_id', flat=True))
        disliked_ids = list(UserDislike.objects.filter(user=user).values_list('disliked_user_id', flat=True))
        
        all_exclude = set(liked_ids + disliked_ids + (exclude_ids or []))
        
        # Get filtered queryset
        queryset = MatchFinder.get_filtered_users(user, filters, list(all_exclude))
        
        # Calculate total before pagination
        total_count = queryset.count()
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        page_queryset = queryset[start:end]
        
        # Annotate with scores
        results = MatchFinder.annotate_with_scores(user, page_queryset)
        
        # Sort by compatibility if requested
        filter_type = (filters or {}).get('filter_type', 'all')
        if filter_type == 'compatible':
            results.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # Check if there are more results
        has_more = total_count > end
        
        return {
            'users': results,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'has_more': has_more,
        }