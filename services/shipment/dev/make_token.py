"""Create a test JWT to call the Shipment API while the Auth service is not running. Development only.

python -m dev.make_token MANAGER
python -m dev.make_token AUTHORIZED_STAFF
Reads JWT_SECRET from the environment; it must match the JWT_SECRET of the running Shipment.
"""
import os
import sys
import time

import jwt

USERS = {"MANAGER": "1", "AUTHORIZED_STAFF": "2", "STAFF": "3"}

if __name__ == "__main__":
    role = sys.argv[1] if len(sys.argv) > 1 else "MANAGER"
    if role not in USERS:
        sys.exit(f"Vai trò phải là một trong: {', '.join(USERS)}")
    claims = {"sub": USERS[role], "role": role, "exp": int(time.time()) + 8 * 3600}
    print(jwt.encode(claims, os.environ["JWT_SECRET"], algorithm="HS256"))
