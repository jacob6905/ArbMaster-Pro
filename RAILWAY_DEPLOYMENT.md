# Railway Deployment Guide for ArbMaster Pro

This guide will help you deploy both the Next.js frontend and Python backend to Railway.

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. GitHub repository connected (already done ✅)
3. WalletConnect Project ID (get from https://cloud.walletconnect.com)

## Deployment Steps

### Step 1: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **jacob6905/ArbMaster-Pro**
5. Select branch: **claude/rebuild-arbmaster-pro-OLV6c**

### Step 2: Set Up Backend Service

Railway will auto-detect the Python app and create a service.

**Backend Configuration:**
1. Service will auto-detect as Python
2. Click on the service → **Settings**
3. Set **Root Directory**: Leave as `/` (root)
4. Railway will use `Dockerfile` and `start.sh` automatically

**Environment Variables for Backend:**
```
PORT=8000
DRY_RUN=true
DEBUG=false

# Optional (for future use)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
POLYMARKET_API_KEY=...
KALSHI_EMAIL=...
KALSHI_PASSWORD=...
```

**Domain:**
- Railway will generate a URL like: `https://arbmaster-backend-production.up.railway.app`
- Copy this URL - you'll need it for the frontend!

### Step 3: Add Frontend Service

1. In the same Railway project, click **"+ New"**
2. Select **"GitHub Repo"** → Same repository
3. Click **"Add Service"**

**Frontend Configuration:**
1. Click on the new service → **Settings**
2. Set **Root Directory**: `/frontend`
3. Set **Build Command**: `npm run build`
4. Set **Start Command**: `npm run start`

**Environment Variables for Frontend:**
```
# Replace with your actual backend URL from Step 2
NEXT_PUBLIC_API_URL=https://arbmaster-backend-production.up.railway.app

# Replace with your backend URL but with wss://
NEXT_PUBLIC_WS_URL=wss://arbmaster-backend-production.up.railway.app

# Get from https://cloud.walletconnect.com
NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID=your_project_id_here

# Feature flags
NEXT_PUBLIC_ENABLE_LIVE_TRADING=false
NEXT_PUBLIC_ENABLE_FLASH_LOANS=false
```

**Domain:**
- Railway will generate a URL like: `https://arbmaster-frontend-production.up.railway.app`
- This is your live dashboard URL! 🎉

### Step 4: Deploy

1. Both services will auto-deploy when you add them
2. Watch the build logs for any errors
3. Once both show "Active", visit your frontend URL
4. You should see your live dashboard!

## Service URLs

After deployment, you'll have:

- **Frontend**: `https://arbmaster-frontend-production.up.railway.app`
- **Backend API**: `https://arbmaster-backend-production.up.railway.app`
- **API Docs**: `https://arbmaster-backend-production.up.railway.app/docs`
- **WebSocket**: `wss://arbmaster-backend-production.up.railway.app/ws`

## Verification

### Test Backend:
```bash
curl https://your-backend-url.up.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-31T...",
  "uptime_seconds": 123.45,
  "mode": "dry_run",
  "version": "1.0.0"
}
```

### Test Frontend:
Open: `https://your-frontend-url.up.railway.app`

You should see:
- ✅ Dashboard loads
- ✅ Metrics showing
- ✅ Opportunities appearing
- ✅ WebSocket connected indicator

## Troubleshooting

### Backend Issues:

**Build fails:**
- Check logs in Railway dashboard
- Verify `requirements.txt` has all dependencies
- Check Python version (should be 3.11+)

**Service crashes:**
- Check environment variables are set
- Look at deployment logs
- Verify PORT is set to 8000

### Frontend Issues:

**Build fails:**
- Check Node version (needs 18+)
- Verify all dependencies in `package.json`
- Check build logs for TypeScript errors

**Can't connect to backend:**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Make sure it's the full URL with `https://`
- Check CORS settings in backend allow your frontend domain

**WebSocket won't connect:**
- Use `wss://` not `ws://` for production
- Verify backend WebSocket endpoint is working: `/ws`
- Check browser console for connection errors

## Custom Domains (Optional)

### Frontend:
1. In Railway → Frontend Service → Settings → Networking
2. Click "Generate Domain" for free `.railway.app` domain
3. Or add custom domain (requires DNS setup)

### Backend:
1. In Railway → Backend Service → Settings → Networking
2. Click "Generate Domain"
3. Update frontend `NEXT_PUBLIC_API_URL` with new domain

## Monitoring

Railway provides:
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time logs for debugging
- **Deployments**: History of all deployments
- **Health Checks**: Automatic health monitoring

Access all from Railway dashboard for each service.

## Updating Your App

Automatic deployment on push:
```bash
git add .
git commit -m "feat: update feature"
git push origin claude/rebuild-arbmaster-pro-OLV6c
```

Railway will automatically:
1. Detect the push
2. Build both services
3. Deploy new versions
4. Zero-downtime deployment

## Cost Estimate

Railway free tier includes:
- $5 in credits per month
- Good for development/testing
- May need paid plan for production load

Estimated usage:
- Backend: ~$5-10/month
- Frontend: ~$5-10/month
- **Total**: ~$10-20/month

## Security Notes

1. **Never commit** `.env` files
2. Set all secrets in Railway dashboard
3. Keep `DRY_RUN=true` until fully tested
4. Monitor logs for suspicious activity
5. Use environment variables for all API keys

## Next Steps After Deployment

1. Test all features on live URLs
2. Connect real Polymarket/Kalshi APIs (when ready)
3. Set up PostgreSQL database (Railway add-on)
4. Add Redis for caching (Railway add-on)
5. Enable monitoring/alerts
6. Set up custom domain
7. Configure backups

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/jacob6905/ArbMaster-Pro/issues

---

**Ready to deploy?** Follow the steps above and your app will be live in minutes! 🚀
