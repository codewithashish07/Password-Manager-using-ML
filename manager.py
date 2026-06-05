from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

def generate_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print("✅ Encryption key generated.")

def load_key():
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_password(plain_password: str) -> str:
    fernet = Fernet(load_key())
    return fernet.encrypt(plain_password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    fernet = Fernet(load_key())
    return fernet.decrypt(encrypted_password.encode()).decode()