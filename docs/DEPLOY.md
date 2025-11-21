# HCSBot Deployment Guide

## Quick Deployment Commands

### Deploy Frontend Only (after editing React files)
```bash
./deploy-frontend.sh
```
or manually:
```bash
npm run build && pm2 restart hcsbot-frontend
```

### Deploy Everything (backend + frontend + scraper)
```bash
./deploy-all.sh
```
or manually:
```bash
npm run build && pm2 restart all
```

### Individual Service Restarts
```bash
pm2 restart hcsbot-backend    # Python FastAPI backend
pm2 restart hcsbot-frontend   # React frontend (build folder)
pm2 restart hcsbot-scraper    # Web scraper
```

## Important Notes

### React Frontend
⚠️ **IMPORTANT**: After editing files in `/var/www/hcsbot/src/`, you MUST rebuild:
- The frontend serves from `/var/www/hcsbot/build/` (compiled files)
- Source files in `/var/www/hcsbot/src/` are not directly served
- Always run `npm run build` after making changes to React components, CSS, or App.js

### Python Backend
✅ Backend changes take effect immediately with `pm2 restart hcsbot-backend`
- Files: `backend/app.py`, `backend/rag_system.py`, etc.
- No build step required

### Cache Busting
After deployment, users may need to clear browser cache:
- **Desktop**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- **Mobile**: Clear browser cache in settings
- **Or use**: `https://hcsbot.hcsonline.com/?v=TIMESTAMP`

## Development Workflow

1. Edit source files in `/var/www/hcsbot/src/` or `/var/www/hcsbot/backend/`
2. For frontend changes: Run `./deploy-frontend.sh`
3. For backend changes: Run `pm2 restart hcsbot-backend`
4. For everything: Run `./deploy-all.sh`
5. Test changes (may need to clear browser cache)
6. Commit to git: `git add . && git commit -m "message" && git push`

## PM2 Management

```bash
pm2 status                  # View all processes
pm2 logs hcsbot-backend     # View backend logs
pm2 logs hcsbot-frontend    # View frontend logs
pm2 monit                   # Monitor resources
pm2 restart all             # Restart everything
```

## Troubleshooting

**Changes not appearing after deploy?**
1. Check if build completed successfully: `npm run build`
2. Verify PM2 restarted: `pm2 status`
3. Clear browser cache completely
4. Check browser console for errors (F12)

**Build fails?**
- Check Node.js version: `node --version` (should be 18.x)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check for syntax errors in source files

**PM2 process crashed?**
- View logs: `pm2 logs hcsbot-backend --lines 50`
- Restart: `pm2 restart hcsbot-backend`
- Check Python errors or missing dependencies
