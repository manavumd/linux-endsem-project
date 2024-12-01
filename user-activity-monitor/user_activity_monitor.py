import os
import time
import json
from datetime import datetime, timezone

LOG_FILE = "/var/log/user_activity.log"

# Global variables to track the last read position
last_auth_log_pos = 0
last_audit_log_pos = 0

def log_event(event_type, user, details=""):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user": user,
        "host": os.uname()[1],
        "details": details
    }
    with open(LOG_FILE, "a") as logfile:
        logfile.write(json.dumps(event) + "\n")

def monitor_login_logout():
    global last_auth_log_pos
    with open("/var/log/auth.log", "r") as f:
        f.seek(last_auth_log_pos)
        lines = f.readlines()
        last_auth_log_pos = f.tell()

        for line in lines:
            if "session opened" in line:
                user = line.split(" ")[-1].strip()
                log_event("login", user)
            elif "session closed" in line:
                user = line.split(" ")[-1].strip()
                log_event("logout", user)

def monitor_commands():
    global last_audit_log_pos
    with open("/var/log/audit/audit.log", "r") as f:
        f.seek(last_audit_log_pos)
        lines = f.readlines()
        last_audit_log_pos = f.tell()

        for line in lines:
            if "exe=" in line:
                cmd = line.split("exe=")[-1].split(" ")[0].strip('"')
                user = line.split("AUID=")[-1].split(" ")[0].strip('"')
                log_event("command", user, details=cmd)

def setup_audit_rules():
    # Add the audit rule only once
    os.system("auditctl -w /bin -p war")

def main():
    setup_audit_rules()
    while True:
        monitor_login_logout()
        monitor_commands()
        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()
