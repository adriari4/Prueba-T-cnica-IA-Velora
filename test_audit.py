import requests
import time
import sys

# Wait for server to start
time.sleep(3)

url = "http://127.0.0.1:8000/audit"

try:
    print(f"Testing {url}...")
    response = requests.post(url)
    if response.status_code == 200:
        print("Success!")
        print("Response:", response.json())
    else:
        print("Failed with status:", response.status_code)
        print("Response:", response.text)
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
