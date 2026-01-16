import json
import logging
import requests

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Attempt to register a webhook/callback URL with the MegaPay provider (best-effort).' 

    def add_arguments(self, parser):
        parser.add_argument('--url', help='Public callback base URL to register (e.g. https://xyz.ngrok.io/payments/_megapay_stub)')
        parser.add_argument('--dry-run', action='store_true', help='Do not POST, just print what would be done')

    def handle(self, *args, **options):
        base = getattr(settings, 'MEGAPAY_BASE_URL', None)
        api_key = getattr(settings, 'MEGAPAY_API_KEY', None)
        if not base or not api_key:
            raise CommandError('MEGAPAY_BASE_URL and MEGAPAY_API_KEY must be set in settings to register webhooks')

        public_base = options.get('url') or getattr(settings, 'LOCAL_MEGAPAY_STUB_URL', None)
        if not public_base:
            raise CommandError('No public URL supplied; pass --url or set LOCAL_MEGAPAY_STUB_URL in settings/.env')

        # Candidate endpoints on provider to attempt registration (best-effort)
        candidates = [
            f"{base.rstrip('/')}/webhooks",
            f"{base.rstrip('/')}/hooks",
            f"{base.rstrip('/')}/notifications",
            f"{base.rstrip('/')}/callbacks",
            f"{base.rstrip('/')}/webhook/register",
            f"{base.rstrip('/')}/api/v1/webhooks",
        ]

        payload = {
            'url': f"{public_base.rstrip('/')}/mpesa-callback/",
            'events': ['mpesa.payment.completed', 'mpesa.payment.failed'],
        }

        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

        self.stdout.write(self.style.NOTICE('Attempting to register webhook for: %s' % payload['url']))

        if options.get('dry_run'):
            self.stdout.write(self.style.SUCCESS('Dry run; would POST to candidates:'))
            for c in candidates:
                self.stdout.write(' - ' + c)
            return

        for url in candidates:
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=8)
                if resp.status_code in (200, 201, 202):
                    self.stdout.write(self.style.SUCCESS(f'Registered webhook at {url} (status {resp.status_code})'))
                    try:
                        self.stdout.write(json.dumps(resp.json(), indent=2))
                    except Exception:
                        self.stdout.write(resp.text[:1000])
                    return
                else:
                    self.stdout.write(self.style.WARNING(f'Attempt to register at {url} returned status {resp.status_code}'))
            except Exception as e:
                logger.debug('Error posting to %s: %s', url, str(e))

        raise CommandError('Failed to register webhook with any candidate endpoint. Check provider docs or supply a concrete URL.')
