# Cloudflare DNS Setup for Tunnel

## CNAME Record Configuration

When pointing to a `trycloudflare.com` tunnel URL, use these settings:

### ❌ WRONG (Don't do this):
- **Name**: `api`
- **Target**: `forming-manor-signatures-equally.trycloudflare.com`
- **Proxy status**: ✅ Proxied (orange cloud)

### ✅ CORRECT (Do this):
- **Name**: `api`  
- **Target**: `forming-manor-signatures-equally.trycloudflare.com`
- **Proxy status**: 🔄 DNS only (gray cloud)

## Why DNS Only?

1. **No Double Proxying**: The tunnel URL is already proxied through Cloudflare
2. **Avoid Conflicts**: Proxying a proxy can cause connection issues
3. **Simpler Routing**: Direct DNS resolution to the tunnel endpoint

## Steps:

1. Go to Cloudflare Dashboard → Your domain → DNS
2. Add CNAME record with settings above
3. Make sure the cloud is **GRAY** (DNS only)
4. Save the record

The tunnel will handle all the Cloudflare optimization automatically!