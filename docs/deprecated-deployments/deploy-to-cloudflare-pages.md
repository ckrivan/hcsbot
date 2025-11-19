# Deploy HCS Chatbot to Cloudflare Pages

## Option 1: Direct Upload (Recommended)

### 1. Go to Cloudflare Pages
- Visit: https://dash.cloudflare.com/
- Go to **"Pages"** in the left sidebar
- Click **"Create a project"**

### 2. Choose Upload Method
- Select **"Upload assets"** (not Git integration)
- Click **"Create project"**

### 3. Upload Your Build
- **Project name**: `hcs-chatbot` (or whatever you prefer)
- **Upload folder**: Select your entire `build` folder
- Click **"Deploy site"**

### 4. Custom Domain Setup
- After deployment, go to **"Custom domains"**
- Add `llm.tektest.org` as a custom domain
- Update your DNS to point to Cloudflare Pages

## Option 2: Using Wrangler CLI (Command Line)

### Install Wrangler
```bash
npm install -g wrangler
```

### Login to Cloudflare
```bash
wrangler login
```

### Deploy
```bash
# From your project directory
wrangler pages deploy build --project-name=hcs-chatbot
```

## Benefits of Cloudflare Pages:

✅ **Automatic HTTPS**
✅ **Global CDN** 
✅ **Automatic caching** (but you control cache invalidation)
✅ **Custom domains** (llm.tektest.org)
✅ **Fast deployment** (minutes, not hours)
✅ **Version history** (rollback if needed)
✅ **Environment variables** support
✅ **Free tier** (plenty for your usage)

## After Deployment:

1. **Test the new URL** Cloudflare gives you
2. **Set up custom domain** (llm.tektest.org)
3. **Update DNS** to point to Cloudflare Pages
4. **Test mobile connections**

This would eliminate your current web server issues and give you a professional deployment platform!

## Current Setup vs Cloudflare Pages:

**Current**: Web Server → Cloudflare Tunnel → llm.tektest.org
**New**: Cloudflare Pages → llm.tektest.org

Much simpler and more reliable!