#!/bin/bash

LOG_FILE="/var/log/user_activity.log"
PROMPT_COMMAND='history 1 | { read x cmd; echo "{\"timestamp\": \"$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\", \"event_type\": \"command\", \"user\": \"$(whoami)\", \"host\": \"$(hostname)\", \"details\": \"${cmd}\"}" >> /var/log/user_activity.log; }'

# Ensure the log file exists and is writable by all users
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE"
    echo "Log file created at $LOG_FILE"
fi

# Loop through all home directories and update .bashrc
for home_dir in /home/*; do
    if [ -d "$home_dir" ]; then
        user=$(basename "$home_dir")
        bashrc="$home_dir/.bashrc"

        # Check if .bashrc exists
        if [ ! -f "$bashrc" ]; then
            touch "$bashrc"
        fi

        # Check if PROMPT_COMMAND is already present
        if grep -q "PROMPT_COMMAND" "$bashrc"; then
            echo "PROMPT_COMMAND already exists in $bashrc for user $user"
        else
            echo -e "\nexport PROMPT_COMMAND='$PROMPT_COMMAND'" >> "$bashrc"
            echo "Added PROMPT_COMMAND to $bashrc for user $user"
        fi
    fi
done

# Handle root user's .bashrc
if [ -f "/root/.bashrc" ]; then
    if grep -q "PROMPT_COMMAND" /root/.bashrc; then
        echo "PROMPT_COMMAND already exists in /root/.bashrc"
    else
        echo -e "\nexport PROMPT_COMMAND='$PROMPT_COMMAND'" >> /root/.bashrc
        echo "Added PROMPT_COMMAND to /root/.bashrc"
    fi
fi

echo "PROMPT_COMMAND setup complete for all users."
