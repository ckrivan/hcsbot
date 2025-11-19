# Vercel Deployment Setup

## Environment Variables
Set these in your Vercel dashboard under Settings > Environment Variables:

- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key  
- `LLM_PROVIDER` - Set to "openai" or "anthropic"
- `USE_LOCAL_LLM` - Set to "false"
- `USE_OLLAMA` - Set to "false"

## Deployment Commands

Using your API token:
```bash
npx vercel --token 1nPmWTcd4seOXfVXDSAbl661
```

Or deploy via GitHub integration after connecting your repository to Vercel.

## Configuration
- Frontend: React app builds to `/build` directory
- Backend: Python Flask app in `/backend/app.py` 
- API routes: All `/api/*` requests route to the backend
- Static routes: All other requests serve the React app