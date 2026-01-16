from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reconcile pending transactions with provider (skeleton).'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-mins', type=int, default=10)

    def handle(self, *args, **options):
        mins = options['older_than_mins']
        cutoff = timezone.now() - timezone.timedelta(minutes=mins)
        pending = Transaction.objects.filter(status='pending', created_at__lt=cutoff)
        self.stdout.write(f'Found {pending.count()} pending transactions older than {mins} minutes')
        for t in pending:
            # TODO: call provider API to check transaction status and either mark completed
            # or failed based on provider response. This is a skeleton so we only log.
            logger.info('Reconciling txn id=%s mpesa_code=%s user=%s created_at=%s', t.pk, t.mpesa_code, t.user_id, t.created_at)
            self.stdout.write(f'Reconciling {t.pk} (mpesa_code={t.mpesa_code})')
