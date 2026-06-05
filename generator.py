import secrets
import string
import math

def calculate_entropy(password: str) -> float:
    charset = 0
    if any(c.islower() for c in password): charset += 26
    if any(c.isupper() for c in password): charset += 26
    if any(c.isdigit() for c in password): charset += 10
    if any(c in string.punctuation for c in password): charset += 32
    return round(len(password) * math.log2(charset), 2) if charset else 0

def generate_password(length=16, use_upper=True, use_digits=True, use_special=True) -> str:
    chars = string.ascii_lowercase
    if use_upper:   chars += string.ascii_uppercase
    if use_digits:  chars += string.digits
    if use_special: chars += "!@#$%^&*"

    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase) if use_upper else "",
        secrets.choice(string.digits) if use_digits else "",
        secrets.choice("!@#$%^&*") if use_special else "",
    ]
    password += [secrets.choice(chars) for _ in range(length - len(password))]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def suggest_passwords(count=3) -> list:
    return [generate_password() for _ in range(count)]