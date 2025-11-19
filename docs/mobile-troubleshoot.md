# Mobile Connection Troubleshooting Guide

## Common Issues & Solutions

### 1. **Cloudflare SSL/TLS Settings**
The most likely culprit! Check your Cloudflare settings:
- Go to Cloudflare Dashboard → SSL/TLS → Overview
- **Set to "Full (strict)" or "Full"** - NOT "Flexible"
- Flexible mode can cause redirect loops on mobile

### 2. **WebSocket Support**
If using WebSockets, Cloudflare requires:
- Go to Network tab in Cloudflare
- Enable WebSockets support

### 3. **Check Backend is Running**
Test the API directly from mobile browser:
```
https://api.tektest.org/health
```
Should return JSON with status info.

### 4. **Mobile Browser Console**
On iPhone/iPad:
1. Settings → Safari → Advanced → Web Inspector (ON)
2. Connect to Mac, open Safari → Develop menu
3. Select your device and inspect console

On Android:
1. Chrome → chrome://inspect
2. Connect via USB with debugging enabled

### 5. **Test with Different Networks**
- Try cellular vs WiFi
- Some corporate/school WiFi blocks custom ports

### 6. **Cloudflare Tunnel Configuration**
Ensure your tunnel is configured correctly:
```bash
# Backend tunnel should be:
cloudflared tunnel --url http://localhost:8000

# NOT http://0.0.0.0:8000 (can cause issues)
```

### 7. **Security Headers**
Add to backend for better mobile compatibility:
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 8. **Quick Test**
Create a simple test endpoint in backend:
```python
@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "timestamp": str(datetime.now())}
```

Then test from mobile: https://api.tektest.org/test

## Deployment Checklist for Mobile Support

- [ ] Backend running on port 8000
- [ ] Cloudflare tunnel active for backend
- [ ] Frontend build with production API URL
- [ ] Cloudflare SSL set to "Full" or "Full (strict)"
- [ ] CORS allows all origins (*)
- [ ] Both frontend and backend use HTTPS
- [ ] No mixed content (HTTP resources on HTTPS page)
- [ ] WebSockets enabled in Cloudflare (if needed)

## Debug Commands

Check if backend is accessible:
```bash
curl -I https://api.tektest.org/health
```

Check CORS headers:
```bash
curl -I -X OPTIONS https://api.tektest.org/health \
  -H "Origin: https://llm.tektest.org" \
  -H "Access-Control-Request-Method: GET"
```

## Most Common Fix
**90% of mobile issues are solved by:**
1. Cloudflare SSL/TLS → Set to "Full" (not Flexible)
2. Clear Cloudflare cache
3. Restart backend with updated CORS settings