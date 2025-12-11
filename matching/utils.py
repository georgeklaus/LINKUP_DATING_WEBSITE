from django.db.models import Q
from users.models import CustomUser

class MatchFinder:
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
        ).exclude(id=user.id)
    
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