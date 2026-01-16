from django.contrib import admin
from .models import CoinPackage, Transaction, ProfileView, RawWebhook
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from . import utils

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


@admin.register(RawWebhook)
class RawWebhookAdmin(admin.ModelAdmin):
    list_display = ('provider', 'provider_reference', 'processed', 'received_at', 'processed_at')
    list_filter = ('provider', 'processed', 'received_at')
    search_fields = ('provider_reference',)
    readonly_fields = ('payload', 'headers', 'received_at', 'processed_at')
    actions = ['process_selected', 'mark_as_failed']

    def process_selected(self, request, queryset):
        processed = 0
        for hook in queryset:
            try:
                ok = utils.process_raw_webhook(hook)
                if ok:
                    processed += 1
            except Exception:
                self.message_user(request, f'Failed to process webhook {hook.pk}', level=messages.ERROR)
        self.message_user(request, f'Processed {processed} webhooks')
    process_selected.short_description = 'Process selected webhooks'

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'Marked {updated} webhooks as processed (failed)')
    mark_as_failed.short_description = 'Mark selected webhooks as failed/processed'

@admin.register(ProfileView)
class ProfileViewAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'viewed_user', 'cost', 'created_at')
    list_filter = ('created_at',)