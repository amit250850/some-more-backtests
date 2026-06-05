import sys
from kiteconnect import KiteConnect

API_KEY = "66zl2ugdl1n2253v"
API_SECRET = "j61w2syt5uagpy9qqndck2jhir61gno9"

request_token = sys.argv[1]

kite = KiteConnect(api_key=API_KEY)
try:
    data = kite.generate_session(request_token, api_secret=API_SECRET)
    print(data)
except Exception as e:
    print(f"Error: {e}")
