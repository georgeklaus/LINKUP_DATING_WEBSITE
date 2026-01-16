# Expose local callbacks with ngrok

This document explains how to expose your local Django server so payment providers can POST webhooks to your development machine.

Prerequisites
- Install ngrok: https://ngrok.com/download
- Have your Django server running on port 7000 (or change the port when using the management command).

Quick manual steps

1. Start your Django server (example with virtualenv):

```fish
source .venv/bin/activate.fish
python manage.py runserver 0.0.0.0:7000
```

2. Start ngrok (in another terminal):

```fish
ngrok http 7000
```

3. Note the public URL printed by ngrok (starts with `https://`).
4. In your payment provider sandbox, set the webhook/callback URL to:

```
<NGROK_PUBLIC_URL>/payments/_megapay_stub/mpesa/transaction-status
```

Automated helper

We added a Django management command: `manage.py ngrok_tunnel`.

- To start ngrok from the command and wait for the public URL (requires `ngrok` in PATH):

```fish
python manage.py ngrok_tunnel --start --set-env
```

- This will start `ngrok http 7000`, discover the public URL via the local ngrok API, and write `LOCAL_MEGAPAY_STUB_URL` to your `.env` (so settings pick it up).

Testing callbacks

- Trigger the dev stub callback for a transaction via:

```fish
curl -X POST -H 'Content-Type: application/json' -d '{"txn_id": 20}' <NGROK_PUBLIC_URL>/payments/_megapay_stub/trigger-callback/
```

- Or POST a status query to the provider-status endpoint:

```fish
curl -X POST -H 'Content-Type: application/json' -d '{"merchant_request_id":"stub_..."}' <NGROK_PUBLIC_URL>/payments/_megapay_stub/mpesa/transaction-status
```

Security note

- Only use ngrok for development/testing. For production you must expose a stable HTTPS endpoint and enforce webhook signature verification and IP allowlists.
