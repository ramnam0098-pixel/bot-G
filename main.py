import os
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(redirect_slashes=True) # Re-enabling to handle common user errors

@app.get("/")
async def root():
    return {"status": "online"}

@app.post("/webhook")
@app.post("/webhook/")
async def handle_webhook(request: Request):
    # Retrieve body for debugging
    body = await request.json()
    
    # Validate passphrase
    expected_pass = os.getenv("WEBHOOK_PASSPHRASE")
    if body.get("passphrase") != expected_pass:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    print(f"Received request: {body}")
    return {"status": "success"}