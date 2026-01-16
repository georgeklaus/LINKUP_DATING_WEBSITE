import os
import time
import json
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Start ngrok (if available) or read ngrok API to obtain public tunnel URL for local callbacks.'

    def add_arguments(self, parser):
        parser.add_argument('--start', action='store_true', help='Start ngrok process (requires ngrok installed)')
        parser.add_argument('--timeout', type=int, default=10, help='Seconds to wait for ngrok to announce tunnels')
        parser.add_argument('--set-env', action='store_true', help='Write LOCAL_MEGAPAY_STUB_URL to .env using the discovered public URL')
        parser.add_argument('--port', type=int, default=7000, help='Local port the Django server is listening on')

    def handle(self, *args, **options):
        start = options['start']
        timeout = options['timeout']
        set_env = options['set_env']
        port = options['port']

        # If requested, start ngrok in the background
        if start:
            try:
                # Start ngrok http <port> if not already running
                subprocess.Popen(['ngrok', 'http', str(port), '--log=stdout'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.stdout.write(self.style.SUCCESS('Started ngrok (background). Waiting for tunnel to appear...'))
            except FileNotFoundError:
                raise CommandError('ngrok binary not found in PATH. Install ngrok and try again: https://ngrok.com/download')

        # Poll ngrok's local API for tunnels
        api = 'http://127.0.0.1:4040/api/tunnels'
        deadline = time.time() + timeout
        public_url = None
        import requests

        while time.time() < deadline:
            try:
                resp = requests.get(api, timeout=2)
                data = resp.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    # Prefer https tunnel
                    https = next((t for t in tunnels if t.get('proto') == 'https'), tunnels[0])
                    public_url = https.get('public_url')
                    break
            except Exception:
                pass
            time.sleep(0.5)

        if not public_url:
            raise CommandError('Could not find ngrok tunnel. Is ngrok running?')

        # Compose the megapay base path we use in settings
        stub_path = f"{public_url.rstrip('/')}/payments/_megapay_stub"
        self.stdout.write(self.style.NOTICE(f'Found ngrok public URL: {public_url}'))
        self.stdout.write(self.style.SUCCESS(f'Using local stub base URL: {stub_path}'))

        if set_env:
            # Update .env in project root
            env_path = Path.cwd() / '.env'
            if not env_path.exists():
                self.stdout.write(self.style.WARNING('.env not found in project root; creating one'))
                env_path.write_text('')

            lines = env_path.read_text().splitlines()
            key = 'LOCAL_MEGAPAY_STUB_URL'
            new_value = f'{stub_path}'
            found = False
            for i, line in enumerate(lines):
                if line.startswith(key + '='):
                    lines[i] = f'{key}={new_value}'
                    found = True
                    break
            if not found:
                lines.append(f'{key}={new_value}')

            env_path.write_text('\n'.join(lines) + '\n')
            self.stdout.write(self.style.SUCCESS(f'Wrote {key} to .env'))

        # Print manual instructions
        self.stdout.write('Next steps:')
        self.stdout.write(f'- Ensure your Django server is reachable on port {port} (runserver or Daphne).')
        self.stdout.write(f'- Configure your payment provider sandbox to use {stub_path} as the callback base (e.g. MEGAPAY callback endpoint).')
        self.stdout.write(f'- You can test by POSTing to {stub_path}/mpesa/transaction-status or {stub_path}/trigger-callback/')
