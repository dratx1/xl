import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

is_anu = os.path.join(os.path.dirname(__file__), "unlock_status.json")
anu_aes = b'barbex_id_secret!'


def encrypt_base64(data: dict) -> str:
    raw = json.dumps(data).encode()
    cipher = AES.new(anu_aes, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(raw, AES.block_size))
    return base64.b64encode(encrypted).decode()

def decrypt_base64(encoded_data: str) -> dict:
    try:
        encrypted = base64.b64decode(encoded_data.encode())
        cipher = AES.new(anu_aes, AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
        return json.loads(decrypted.decode())
    except Exception:
        return {"is_unlocked": False}

def load_status():
    if not os.path.exists(is_anu):
        return {"is_unlocked": False}
    try:
        with open(is_anu, "r") as f:
            encoded_data = f.read().strip()
        return decrypt_base64(encoded_data)
    except Exception:
        return {"is_unlocked": False}

def save_status(status: bool):
    try:
        encoded = encrypt_base64({"is_unlocked": status})
        with open(is_anu, "w") as f:
            f.write(encoded)
    except Exception:
        pass
