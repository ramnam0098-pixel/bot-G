from fastapi import FastAPI, Request, HTTPException
from bot.notifier import send_discord_signal
# Import your logic modules here
# from bot.analysis import analyze_market 

app = FastAPI(redirect_slashes=False)
# 1. Health check for verifying server status
@app.get("/")
async def root():
    return {"status": "online", "message": "Gateway active"}

# 2. Webhook endpoint
@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # Simple passphrase validation
    # Ensure WEBHOOK_PASSPHRASE is set in Render Environment Variables
    import os
    expected_pass = os.getenv("WEBHOOK_PASSPHRASE")
    
    if data.get("passphrase") != expected_pass:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Process your bot logic here
    # Example: send_discord_signal(data)
    
    return {"status": "received", "data": data}