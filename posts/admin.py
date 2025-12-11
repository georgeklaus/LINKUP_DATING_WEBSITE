from django.contrib import admin
from .models import Post, Comment, Like

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'user__username')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_preview', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    
    def post_preview(self, obj):
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content
    post_preview.short_description = 'Post'
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post_preview', 'created_at')
    list_filter = ('created_at',)
    
    def post_preview(self, obj):
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content
    post_preview.short_description = 'Post'