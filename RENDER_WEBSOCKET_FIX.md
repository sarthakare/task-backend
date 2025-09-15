# Render.com WebSocket Configuration Fix

## Issue
WebSocket connections to `wss://task-backend-ed5i.onrender.com/ws` are failing with connection errors.

## Root Cause
Render.com requires specific configuration for WebSocket support, and there might be issues with:
1. **Service Configuration**: Render.com services need to be configured as "Web Services" (not "Background Workers")
2. **Port Configuration**: The service needs to bind to the correct port
3. **Startup Command**: The startup command needs to be configured properly

## Solutions

### Solution 1: Update Render.com Service Configuration

1. **Go to your Render.com dashboard**
2. **Select your backend service**
3. **Go to Settings → Environment**
4. **Update the following settings:**

```bash
# Environment Variables
PYTHON_VERSION=3.11

# Build Command
pip install -r requirements.txt

# Start Command
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Solution 2: Update main.py for Render.com

Add this configuration to your `main.py`:

```python
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Get port from environment (required for Render.com)
port = int(os.environ.get("PORT", 8000))

# ... rest of your code ...

# Add this at the end of main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Solution 3: Create render.yaml (Recommended)

Create a `render.yaml` file in your backend root:

```yaml
services:
  - type: web
    name: task-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
```

### Solution 4: Test WebSocket with wscat

Install wscat to test the connection:
```bash
npm install -g wscat
wscat -c wss://task-backend-ed5i.onrender.com/ws
```

## Alternative: Use a Different Hosting Platform

If Render.com continues to have WebSocket issues, consider:

### Railway (Recommended for WebSockets)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Heroku
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git push heroku main
```

## Testing Steps

1. **Deploy with updated configuration**
2. **Test HTTP endpoint**: `curl https://task-backend-ed5i.onrender.com/health`
3. **Test WebSocket**: Use browser dev tools or wscat
4. **Check logs**: Monitor Render.com logs for errors

## Common Issues

- **Port binding**: Must bind to `0.0.0.0:$PORT`
- **Service type**: Must be "Web Service" not "Background Worker"
- **Startup command**: Must use uvicorn with proper host/port
- **Environment variables**: PORT variable is required

## Next Steps

1. Update your Render.com service configuration
2. Redeploy the backend
3. Test the WebSocket connection
4. If issues persist, consider migrating to Railway or Heroku
