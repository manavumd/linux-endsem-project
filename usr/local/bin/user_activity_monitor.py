import os
import json
import time
from datetime import datetime, timezone
import subprocess

LOG_FILE = "/var/log/user_activity.log"
last_auth_log_pos = 0
processed_login_events = set()

def log_event(event_type, user, details=""):
    """Log events to the centralized log file."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user": user.strip(),
        "host": os.uname()[1],
        "details": details.strip(),
        "count": 1
    }
    with open(LOG_FILE, "a") as logfile:
        logfile.write(json.dumps(event) + "\n")

def monitor_login_logout():
    global last_auth_log_pos, processed_login_events
    with open("/var/log/auth.log", "r") as f:
        # Start reading from the end of the file if it's the first run
        if last_auth_log_pos == 0:
            f.seek(0, os.SEEK_END)
        else:
            f.seek(last_auth_log_pos)

        lines = f.readlines()
        last_auth_log_pos = f.tell()

        for line in lines:
            if "session opened" in line:
                user_raw = line.split(" ")[-1].strip()
                user = user_raw.split("(")[0]
                event_id = f"login-{user}"
                if event_id not in processed_login_events:
                    processed_login_events.add(event_id)
                    log_event("login", user)
                    #configure_prompt_command(user)
            elif "session closed" in line:
                user_raw = line.split(" ")[-1].strip()
                user = user_raw.split("(")[0]
                event_id = f"logout-{user}"
                if event_id not in processed_login_events:
                    processed_login_events.add(event_id)
                    log_event("logout", user)


def configure_prompt_command(user):
    """Configure PROMPT_COMMAND for the specified user."""
    logging_cmd = (
        'history 1 | { read x cmd; echo "{\\"timestamp\\": \\"$(date -u +\\"%Y-%m-%dT%H:%M:%SZ\\")\\", '
        '\\"event_type\\": \\"command\\", \\"user\\": \\"$(whoami)\\", \\"host\\": \\"$(hostname)\\", '
        '\\"details\\": \\"${cmd}\\"}" >> /var/log/user_activity.log; }'
    )
    user_bashrc = f"/home/{user}/.bashrc"

    # Check if the file exists
    if os.path.exists(user_bashrc):
        # Read the .bashrc file to check if PROMPT_COMMAND already exists
        with open(user_bashrc, "r") as f:
            lines = f.readlines()

        if any("PROMPT_COMMAND" in line for line in lines):
            log_event("info", user, f"PROMPT_COMMAND already exists for {user}")
            return  # Skip adding if it already exists

        # Append PROMPT_COMMAND if not already present
        with open(user_bashrc, "a") as f:
            f.write(f"\nexport PROMPT_COMMAND='{logging_cmd}'\n")
        log_event("info", user, f"PROMPT_COMMAND configured for {user}")

        # Automatically source the updated .bashrc
        try:
            subprocess.run(["su", "-", user, "-c", "source ~/.bashrc"], check=True)
            log_event("info", user, f".bashrc sourced for {user}")
        except subprocess.CalledProcessError as e:
            log_event("error", user, f"Failed to source .bashrc: {e}")


def ensure_log_file_exists():
    """Ensure the log file exists and is writable by all."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w"):
            pass
    os.chmod(LOG_FILE, 0o666)  # Allow read/write access for all users

def main():
    ensure_log_file_exists()
    print(f"Monitoring login/logout and commands. Logs stored in {LOG_FILE}")
    while True:
        monitor_login_logout()
        time.sleep(10)

if __name__ == "__main__":
    main()
