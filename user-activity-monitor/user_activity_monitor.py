import os
import time
import json
from datetime import datetime, timezone

LOG_FILE = "/var/log/user_activity.log"
last_auth_log_pos = 0
last_audit_log_pos = 0
processed_events = set()
processed_login_events = set()

def log_event(event_type, user, details=""):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user": user.strip(),
        "host": os.uname()[1],
        "details": details.strip()
    }
    with open(LOG_FILE, "a") as logfile:
        logfile.write(json.dumps(event) + "\n")

def monitor_login_logout():
    global last_auth_log_pos, processed_login_events
    with open("/var/log/auth.log", "r") as f:
        f.seek(last_auth_log_pos)
        lines = f.readlines()
        last_auth_log_pos = f.tell()

        for line in lines:
            if "session opened" in line:
                user = line.split(" ")[-1].strip()
                event_id = f"login-{user}"
                if event_id not in processed_login_events:
                    processed_login_events.add(event_id)
                    log_event("login", user)
            elif "session closed" in line:
                user = line.split(" ")[-1].strip()
                event_id = f"logout-{user}"
                if event_id not in processed_login_events:
                    processed_login_events.add(event_id)
                    log_event("logout", user)

def monitor_commands():
    global last_audit_log_pos, processed_events
    with open("/var/log/audit/audit.log", "r") as f:
        f.seek(last_audit_log_pos)
        lines = f.readlines()
        last_audit_log_pos = f.tell()

        for line in lines:
            if "execve" in line:
                cmd = line.split("exe=")[-1].split(" ")[0].strip('"')
                user = line.split("uid=")[-1].split(" ")[0].strip('"')
                event_id = f"{user}-{cmd}"
                if event_id not in processed_events:
                    processed_events.add(event_id)
                    log_event("command", user, details=cmd)

def setup_audit_rules():
    os.system("auditctl -a always,exit -S execve -F euid>=1000 -F euid!=4294967295 -k user-commands")

def main():
    setup_audit_rules()
    while True:
        monitor_login_logout()
        monitor_commands()
        time.sleep(10)

if __name__ == "__main__":
    main()
