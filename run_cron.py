import time
import subprocess
import sys
from datetime import datetime

print("🕐 Auto-auction ender started...")
print("Press Ctrl+C to stop\n")

while True:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] Checking for expired auctions...")
    subprocess.run([sys.executable, 'manage.py', 'end_auctions'])
    print(f"[{now}] Next check in 60 seconds...\n")
    time.sleep(60)