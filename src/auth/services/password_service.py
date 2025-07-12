import bcrypt

def get_password_hash(password: str) -> str:
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password must not exceed 72 bytes for bcrypt.")
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not isinstance(hashed_password, str):
        return False
    if len(plain_password.encode('utf-8')) > 72:
        raise ValueError("Password must not exceed 72 bytes for bcrypt.")
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
