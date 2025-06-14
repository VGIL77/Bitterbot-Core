# Deploying ENGRAM Module to Production

## Quick Deploy Guide

### 1. Backend Deployment (Railway)

```bash
# From project root
cd backend

# Install Railway CLI if needed
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (first time only)
railway init

# Deploy the engram service
railway up

# Set environment variables
railway variables set ENABLE_ENGRAM_MODULE=true
railway variables set ADMIN_CONSOLE_ENABLED=true
```

### 2. Frontend Deployment (Vercel)

```bash
# Move dashboard files to admin console structure
mkdir -p admin_console/public/modules/engram
cp -r backend/engram_dashboard/* admin_console/public/modules/engram/

# Deploy to Vercel
vercel --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL = your-railway-url.up.railway.app
# NEXT_PUBLIC_WS_URL = your-railway-url.up.railway.app
```

### 3. Update Dashboard Connection

Edit `dashboard.js` to use production URLs:

```javascript
// Change from localhost to production
const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://your-app.up.railway.app';
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://your-app.up.railway.app';
```

### 4. Verify Deployment

1. Check Railway logs:
   ```bash
   railway logs
   ```

2. Test dashboard connection:
   ```
   https://your-admin.vercel.app/modules/engram
   ```

3. Monitor WebSocket connection in browser console

### 5. Production Checklist

- [ ] Database migration applied
- [ ] Environment variables set
- [ ] CORS configured for Vercel domain
- [ ] SSL certificates active
- [ ] Health checks passing
- [ ] Metrics flowing to dashboard
- [ ] Export functionality working

## Troubleshooting

### WebSocket Connection Issues
- Ensure Railway supports WebSocket upgrade
- Check CORS settings include Vercel domain
- Verify SSL certificates are valid

### No Data Showing
- Check database connection
- Verify engram creation is enabled
- Look for errors in Railway logs

### Performance Issues
- Enable Redis caching
- Increase Railway instance size
- Use CDN for static assets

## Monitoring

Once deployed, monitor at:
- Railway Dashboard: Logs, metrics, deploys
- Vercel Dashboard: Function logs, analytics
- Admin Console: Real-time engram metrics

---

Remember: This is production academic research. Every conversation contributes to our paper! 🚀