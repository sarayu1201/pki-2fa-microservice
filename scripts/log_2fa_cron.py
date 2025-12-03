#!/usr/bin/env python3
import pyotp
import base64
import os
from datetime import datetime

SEED_FILE = "/data/seed.txt"

def hex_to_base32(hex_seed: str) -> str:
    seed_bytes = bytes.fromhex(hex_seed)
    base32_seed = base64.b32encode(seed_bytes).decode('utf-8')
    return base32_seed

try:
    if not os.path.exists(SEED_FILE):
        print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Error: Seed file not found", flush=True)
        exit(1)
    
    with open(SEED_FILE, "r") as f:
        hex_seed = f.read().strip()
    
    base32_seed = hex_to_base32(hex_seed)
    totp = pyotp.TOTP(base32_seed, interval=30, digits=6)
    code = totp.now()
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"{timestamp} - 2FA Code: {code}", flush=True)

except Exception as e:
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - Error: {str(e)}", flush=True)
