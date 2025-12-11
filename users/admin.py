from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'gender', 'orientation', 'coins', 'is_online', 'created_at')
    list_filter = ('gender', 'orientation', 'is_online', 'created_at')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('gender', 'orientation', 'bio', 'profile_picture', 'date_of_birth', 'location', 'coins', 'is_online')
        }),
    )

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'occupation', 'education', 'relationship_goals')
    search_fields = ('user__username', 'occupation', 'education')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)