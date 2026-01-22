# Render.com Deployment Guide for Luchat

Complete step-by-step guide to deploy Luchat on Render (free tier).

---

## What You Have

- ✅ **Neon** account (PostgreSQL)
- ✅ **Upstash** account (Redis)
- 🔲 **Render** account (next step)
- 🔲 **GitHub** repo (we'll create this)

---

## Step 1: Get Your Neon Database URL

1. Go to [console.neon.tech](https://console.neon.tech)
2. Select your project (or create one named `luchat`)
3. Go to **Dashboard** → **Connection Details**
4. Make sure **Connection string** is selected
5. Copy the connection string:
   ```
   postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```
   📝 **Save this as DATABASE_URL**

---

## Step 2: Get Your Upstash Redis URL

1. Go to [console.upstash.com](https://console.upstash.com)
2. Select your Redis database (or create one named `luchat-redis`)
3. Scroll to **REST API** section or **Connect** section
4. Copy the **UPSTASH_REDIS_REST_URL** or the Redis URL:
   ```
   rediss://default:xxx@xxx-xxx.upstash.io:6379
   ```
   📝 **Save this as REDIS_URL**

---

## Step 3: Push Code to GitHub

### Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `luchat`
3. Keep it **Private**
4. Click **Create repository**

### Push Your Code

Run these commands in your terminal:

```bash
cd /home/klaus/linkup/luchat

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for Render deployment"

# Add your GitHub repo as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/luchat.git

# Push
git branch -M main
git push -u origin main
```

If asked for credentials, use:
- Username: your GitHub username
- Password: a Personal Access Token (create at github.com/settings/tokens)

---

## Step 4: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **Get Started for Free**
3. Sign up with **GitHub** (easiest!)
4. Authorize Render to access your GitHub

---

## Step 5: Deploy on Render

### Create New Web Service

1. In Render dashboard, click **New** → **Web Service**
2. Connect your GitHub repository:
   - Click **Connect account** if needed
   - Select `luchat` repository
3. Click **Connect**

### Configure Service

| Setting | Value |
|---------|-------|
| **Name** | `luchat` |
| **Region** | Oregon (US West) or closest to you |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate` |
| **Start Command** | `daphne -b 0.0.0.0 -p $PORT luchat.asgi:application` |
| **Instance Type** | **Free** |

### Add Environment Variables

Scroll down to **Environment Variables** and add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Click "Generate" or paste a random 50+ char string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,YOUR_CUSTOM_DOMAIN` |
| `CSRF_TRUSTED_ORIGINS` | `https://luchat.onrender.com,https://YOUR_CUSTOM_DOMAIN` |
| `DATABASE_URL` | Your Neon connection string from Step 1 |
| `REDIS_URL` | Your Upstash Redis URL from Step 2 |
| `CELERY_BROKER_URL` | Same as REDIS_URL |
| `MEGAPAY_API_KEY` | `MGPYl2DC613a` |
| `MEGAPAY_EMAIL` | `georgerubinga@gmail.com` |
| `MEGAPAY_BASE_URL` | `https://megapay.co.ke/backend/v1` |
| `USE_LOCAL_MEGAPAY_STUB` | `False` |
| `PYTHON_VERSION` | `3.11.0` |

**To generate SECRET_KEY locally:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Deploy!

1. Click **Create Web Service**
2. Wait 5-10 minutes for first deployment
3. Watch the logs for any errors

---

## Step 6: Verify Deployment

Once deployed, Render gives you a URL like:
```
https://luchat.onrender.com
```

1. Visit the URL
2. First load may take 30 seconds (free tier spins down)
3. Try registering a new account
4. Test the chat feature (WebSocket)

---

## Step 7: Create Admin User

1. In Render dashboard, go to your `luchat` service
2. Click **Shell** tab (or **Connect** → **Shell**)
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, password

---

## Step 8: Connect Custom Domain (Optional)

1. In Render dashboard → your service → **Settings**
2. Scroll to **Custom Domains**
3. Click **Add Custom Domain**
4. Enter your domain (e.g., `luchat.com` or `www.luchat.com`)
5. Render shows DNS records to add

At your domain registrar:
- Add **CNAME** record: `@` or `www` → `luchat.onrender.com`

Wait 5-30 minutes for DNS propagation.

**Don't forget to update:**
- `ALLOWED_HOSTS` environment variable
- `CSRF_TRUSTED_ORIGINS` environment variable

---

## Step 9: Update MegaPay Webhook

Go to MegaPay dashboard and set webhook URL to:
```
https://luchat.onrender.com/payments/webhook/
```

Or with custom domain:
```
https://YOUR_DOMAIN.com/payments/webhook/
```

---

## About Free Tier "Sleep"

Render free tier **spins down after 15 minutes of inactivity**:
- First visitor after sleep waits ~30 seconds
- After that, it's fast until next sleep
- For a dating/chat app, users will keep it awake!

**Tips:**
- Use a free uptime monitor like [UptimeRobot](https://uptimerobot.com) to ping your site every 14 minutes (keeps it awake)
- Or just accept the occasional 30-second wait

---

## Troubleshooting

### View Logs
Render Dashboard → Your Service → **Logs** tab

### Common Issues

**1. Build fails**
- Check logs for specific error
- Make sure requirements.txt is up to date

**2. Static files not loading**
- Verify `collectstatic` is in build command
- Check `whitenoise` is in MIDDLEWARE

**3. Database connection error**
- Verify DATABASE_URL is correct
- Check Neon dashboard for issues

**4. WebSocket not connecting**
- Render supports WebSockets on free tier
- Check browser console for errors
- Verify ALLOWED_HOSTS includes your domain

**5. Site shows 500 error**
- Check logs for details
- Verify all environment variables are set

---

## Updating Your App

### After code changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Render auto-deploys when you push to main branch!

### Run migrations after model changes:

1. Push code first
2. In Render Shell:
   ```bash
   python manage.py migrate
   ```

---

## Cost Summary

| Service | Cost |
|---------|------|
| Render (free tier) | $0 |
| Neon (free tier) | $0 |
| Upstash (free tier) | $0 |
| **Total** | **$0/month** |

---

## Quick Reference

```
App URL: https://luchat.onrender.com
Render Dashboard: https://dashboard.render.com
Neon Dashboard: https://console.neon.tech
Upstash Dashboard: https://console.upstash.com
MegaPay Webhook: https://luchat.onrender.com/payments/webhook/
```

---

## Keep It Awake (Optional)

Free tier sleeps after 15 min. To prevent this:

1. Go to [uptimerobot.com](https://uptimerobot.com) (free)
2. Create account
3. Add new monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://luchat.onrender.com`
   - Monitoring Interval: 5 minutes
4. Save

This pings your site every 5 minutes, keeping it awake 24/7!
