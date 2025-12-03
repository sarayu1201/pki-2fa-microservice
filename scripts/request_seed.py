#!/usr/bin/env python3
import base64
import json
import requests

API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"

STUDENT_ID = "23P31A1201"
GITHUB_REPO_URL = "https://github.com/sarayu1201/pki-2fa-microservice"


def load_public_key(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        pem = f.read()
    # Keep PEM as-is; requests/json will handle newlines correctly
    return pem


def request_seed():
    public_key_pem = load_public_key("student_public.pem")

    payload = {
        "student_id": STUDENT_ID,
        "github_repo_url": GITHUB_REPO_URL,
        "public_key": public_key_pem,
    }

    headers = {"Content-Type": "application/json"}

    resp = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "success" or "encrypted_seed" not in data:
        raise RuntimeError(f"Unexpected response: {data}")

    encrypted_seed = data["encrypted_seed"]

    with open("encrypted_seed.txt", "w", encoding="utf-8") as f:
        f.write(encrypted_seed)

    print("encrypted_seed.txt created successfully")


if __name__ == "__main__":
    request_seed()
