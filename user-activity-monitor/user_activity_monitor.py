import os
import time
import json
from datetime import datetime

LOG_FILE = "/var/log/user_activity.log"

def log_event(event_type, user, details=""):
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user": user,
        "host": os.uname()[1],
        "details": details
    }
    with open(LOG_FILE, "a") as logfile:
        logfile.write(json.dumps(event) + "\n")

def monitor_login_logout():
    # Check `/var/log/auth.log` or equivalent for login/logout events
    with open("/var/log/auth.log", "r") as f:
        lines = f.readlines()
        for line in lines[-10:]:  # Tail the last 10 lines for example
            if "session opened" in line:
                user = line.split(" ")[-1].strip()
                log_event("login", user)
            elif "session closed" in line:
                user = line.split(" ")[-1].strip()
                log_event("logout", user)

def monitor_commands():
    # Example: Capture commands via audit logs (requires auditd)
    os.system("auditctl -w /bin -p war")  # Monitor commands in `/bin`
    with open("/var/log/audit/audit.log", "r") as f:
        lines = f.readlines()
        for line in lines[-10:]:
            if "exe=" in line:
                cmd = line.split("exe=")[-1].split(" ")[0]
                log_event("command", "unknown", details=cmd)

def main():
    while True:
        monitor_login_logout()
        monitor_commands()
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()
