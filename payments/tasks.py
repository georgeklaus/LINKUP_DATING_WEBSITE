from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Transaction
from .utils import reconcile_transaction_with_provider
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def reconcile_pending_transactions(self, older_than_minutes=10, limit=50):
    """Reconcile pending transactions older than `older_than_minutes` minutes.

    This task queries the payment provider for each pending transaction and applies
    updates (completed/failed) using the reconciliation helper.
    """
    cutoff = timezone.now() - timezone.timedelta(minutes=older_than_minutes)
    qs = Transaction.objects.filter(status='pending', created_at__lt=cutoff).order_by('created_at')[:limit]
    changed = 0
    for txn in qs:
        try:
            ok = reconcile_transaction_with_provider(txn)
            if ok:
                changed += 1
        except Exception as e:
            logger.exception('Error reconciling txn %s: %s', txn.pk, str(e))
    return {'checked': qs.count(), 'changed': changed}
