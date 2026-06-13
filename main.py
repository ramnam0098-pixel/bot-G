import os
import httpx
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

async def send_discord(message: str):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not set")
        return
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"content": message})

@app.post("/webhook")
@app.post("/webhook/")
async def handle_webhook(request: Request):
    data = await request.json()
    
    # 1. Auth Validation
    if data.get("passphrase") != os.getenv("WEBHOOK_PASSPHRASE"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # 2. Process Discord Alert
    msg = f"Alert: {data.get('side')} {data.get('symbol')} at {data.get('price')}"
    await send_discord(msg)
    
    return {"status": "success"}