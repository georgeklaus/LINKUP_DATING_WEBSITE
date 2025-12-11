from django.contrib import admin
from .models import CoinPackage, Transaction, ProfileView

@admin.register(CoinPackage)
class CoinPackageAdmin(admin.ModelAdmin):
    list_display = ('amount', 'coins', 'description', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'amount', 'coins', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'mpesa_code', 'phone_number')
    readonly_fields = ('created_at', 'completed_at')

@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'viewed_user', 'cost', 'created_at')
    list_filter = ('created_at',)