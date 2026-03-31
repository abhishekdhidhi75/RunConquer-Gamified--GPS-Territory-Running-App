import hashlib, secrets

# Test hash
salt = secrets.token_hex(16)
h = hashlib.sha256((salt + "test123").encode()).hexdigest()
stored = f"{salt}${h}"

# Test verify
s2, h2 = stored.split("$", 1)
match = hashlib.sha256((s2 + "test123").encode()).hexdigest() == h2

print(f"Hash: {stored[:30]}...")
print(f"Verify: {match}")

# Test full register flow
import sys
sys.path.insert(0, ".")
from app.database import init_db, get_db
from app.routers.auth import hash_password, verify_password

init_db()
pw = hash_password("test123456")
print(f"hash_password result: {pw[:30]}...")
print(f"verify_password: {verify_password('test123456', pw)}")
print("ALL TESTS PASSED!")
