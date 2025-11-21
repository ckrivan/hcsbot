# HCSBot Credentials Management

## Overview
All authentication credentials are stored securely in the `.env` file, which is excluded from Git version control.

## Current Credentials

### 1. App Access Password (Main Login)
- **Variable:** `REACT_APP_ACCESS_PASSWORD`
- **Current Value:** `I L0V3 P!ZZ@$$$`
- **Used By:** Frontend (src/App.js) for initial app access
- **How to Change:** Update `.env` file and rebuild frontend with `./deploy-frontend.sh`

### 2. Admin Panel Credentials
- **Username Variable:** `ADMIN_USERNAME`
- **Password Variable:** `ADMIN_PASSWORD`
- **Current Username:** `hcs`
- **Current Password:** `I love P!zz@`
- **Used By:** Backend (backend/app.py) for admin panel access
- **How to Change:** Update `.env` file and restart backend with `pm2 restart hcsbot-backend`

## Security Best Practices

### File Permissions
The `.env` file has restricted permissions (600):
```bash
-rw------- 1 root root 617 Nov 20 21:39 /var/www/hcsbot/.env
```
- Only root can read/write
- Not accessible by other users
- Not committed to Git (in .gitignore)

### How to Update Credentials

1. **Edit the .env file:**
   ```bash
   nano /var/www/hcsbot/.env
   ```

2. **Update the desired credentials:**
   ```bash
   # Frontend password
   REACT_APP_ACCESS_PASSWORD=new-password-here

   # Admin credentials
   ADMIN_USERNAME=new-admin-username
   ADMIN_PASSWORD=new-admin-password
   ```

3. **Deploy changes:**
   ```bash
   cd /var/www/hcsbot

   # If you changed REACT_APP_ACCESS_PASSWORD:
   ./deploy-frontend.sh

   # If you changed ADMIN credentials:
   pm2 restart hcsbot-backend
   ```

## Location of Credentials

### In Code (reads from .env):
- **Frontend:** `src/App.js:41` - `process.env.REACT_APP_ACCESS_PASSWORD`
- **Backend:** `backend/app.py:422-423` - Admin login function
- **Backend:** `backend/app.py:434-435` - Admin feedback function

### In .env file:
```
/var/www/hcsbot/.env
```

## Important Notes

1. **React Environment Variables:**
   - Must start with `REACT_APP_`
   - Are baked into the build at compile time
   - Require rebuild after changes (`./deploy-frontend.sh`)

2. **Backend Environment Variables:**
   - Loaded at runtime
   - Only require process restart after changes (`pm2 restart hcsbot-backend`)

3. **Never commit .env to Git:**
   - Already in `.gitignore`
   - Contains sensitive API keys (OpenAI, LiquidWeb, etc.)
   - Keep backups in secure location

## Testing Credentials

### Test Main Login:
1. Visit `https://hcsbot.hcsonline.com`
2. Enter password: `I L0V3 P!ZZ@$$$`
3. Should see chat interface

### Test Admin Panel:
1. After logging in, click "Admin" in the interface
2. Username: `hcs`
3. Password: `I love P!zz@`
4. Should see feedback dashboard

## Troubleshooting

**Problem:** Login fails after credential change
- **Solution:** Make sure you deployed/restarted the correct service
- Frontend changes: Run `./deploy-frontend.sh`
- Backend changes: Run `pm2 restart hcsbot-backend`

**Problem:** .env changes not taking effect
- **Solution:** Check file permissions: `ls -la /var/www/hcsbot/.env`
- Should be `-rw-------` (600)
- Verify PM2 restarted: `pm2 status`

**Problem:** Can't read .env file
- **Solution:** Use sudo: `sudo cat /var/www/hcsbot/.env`
- Only root has access to this file for security
