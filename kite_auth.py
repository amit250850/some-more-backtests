import json
import os
from kiteconnect import KiteConnect

API_KEY = os.environ.get("KITE_API_KEY", "66zl2ugdl1n2253v") # Fallback for demo purposes, remove in production
API_SECRET = os.environ.get("KITE_API_SECRET", "j61w2syt5uagpy9qqndck2jhir61gno9")
SESSION_FILE = "kite_session.json"

def get_kite_session():
    kite = KiteConnect(api_key=API_KEY)

    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                access_token = data.get("access_token")
            kite.set_access_token(access_token)

            # Simple check if session is valid
            kite.profile()
            print("Session valid, authenticated using saved access_token.")
            return kite
        except Exception as e:
            print(f"Session invalid or expired: {e}")

    # Not valid, need new login
    print(f"Please login here: {kite.login_url()}")
    request_token = os.environ.get("KITE_REQUEST_TOKEN")
    if not request_token:
        request_token = input("Enter request_token from redirect URL: ").strip()

    data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]

    kite.set_access_token(access_token)

    with open(SESSION_FILE, "w") as f:
        json.dump({"access_token": access_token}, f)

    print("Session generated and saved.")
    return kite
