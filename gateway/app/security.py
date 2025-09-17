from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_key(plaintext: str) -> str:
    return pwd_context.hash(plaintext)


def verify_key(plaintext: str, key_hash: str) -> bool:
    try:
        return pwd_context.verify(plaintext, key_hash)
    except Exception:
        return False

