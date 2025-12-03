from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import pyotp
import base64
import os
import time

app = FastAPI()

SEED_FILE = "/data/seed.txt"
PRIVATE_KEY_FILE = "student_private.pem"

class EncryptedSeedRequest(BaseModel):
    encrypted_seed: str

class CodeRequest(BaseModel):
    code: str

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def hex_to_base32(hex_seed: str) -> str:
    seed_bytes = bytes.fromhex(hex_seed)
    base32_seed = base64.b32encode(seed_bytes).decode('utf-8')
    return base32_seed

def read_seed() -> str:
    if not os.path.exists(SEED_FILE):
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})
    with open(SEED_FILE, "r") as f:
        return f.read().strip()

@app.post("/decrypt-seed")
async def decrypt_seed(request: EncryptedSeedRequest):
    try:
        private_key = load_private_key()
        encrypted_data = base64.b64decode(request.encrypted_seed)
        
        decrypted_seed = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        hex_seed = decrypted_seed.decode('utf-8')
        
        if len(hex_seed) != 64 or not all(c in '0123456789abcdef' for c in hex_seed):
            raise ValueError("Invalid seed format")
        
        os.makedirs("/data", exist_ok=True)
        
        with open(SEED_FILE, "w") as f:
            f.write(hex_seed)
        
        return {"status": "ok"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

@app.get("/generate-2fa")
async def generate_2fa():
    try:
        hex_seed = read_seed()
        base32_seed = hex_to_base32(hex_seed)
        totp = pyotp.TOTP(base32_seed, interval=30, digits=6)
        code = totp.now()
        current_time = int(time.time())
        time_remaining = 30 - (current_time % 30)
        
        return {
            "code": code,
            "valid_for": time_remaining
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/verify-2fa")
async def verify_2fa(request: CodeRequest):
    if not request.code:
        raise HTTPException(status_code=400, detail={"error": "Missing code"})
    
    try:
        hex_seed = read_seed()
        base32_seed = hex_to_base32(hex_seed)
        totp = pyotp.TOTP(base32_seed, interval=30, digits=6)
        is_valid = totp.verify(request.code, valid_window=1)
        
        return {"valid": is_valid}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
