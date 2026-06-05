import hashlib
import requests

def check_breach(password: str) -> dict:
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    
    try:
        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=5
        )
        if response.status_code != 200:
            return {"breached": False, "count": 0, "error": "API unavailable"}
        
        hashes = (line.split(':') for line in response.text.splitlines())
        for h, count in hashes:
            if h == suffix:
                return {"breached": True, "count": int(count)}
        
        return {"breached": False, "count": 0}

    except Exception as e:
        return {"breached": False, "count": 0, "error": str(e)}