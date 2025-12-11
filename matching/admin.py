from django.contrib import admin
from .models import UserLike, UserDislike, Match, UserView

@admin.register(UserLike)
class UserLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'liked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'liked_user__username')

@admin.register(UserDislike)
class UserDislikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'disliked_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'disliked_user__username')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user1__username', 'user2__username')

@admin.register(UserView)
class UserViewAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'viewed_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('viewer__username', 'viewed_user__username')