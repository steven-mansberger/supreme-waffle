#!/bin/bash

# Gather system metadata
HOSTNAME=$(hostname | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
OS_NAME=$(grep '^NAME=' /etc/os-release | cut -d'"' -f2 | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
OS_VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d'=' -f2 | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
TIMESTAMP=$(date '+%Y-%m-%dT%H-%M-%S')

# Output directory and files with system-specific names and timestamp
BACKUP_DIR="backups/$HOSTNAME"
HUMAN_READABLE="$BACKUP_DIR/system_config_${HOSTNAME}_${OS_NAME}_${TIMESTAMP}.txt"
YAML_OUTPUT="$BACKUP_DIR/system_config_${HOSTNAME}_${OS_NAME}_${TIMESTAMP}.yml"
HOME_DIR="$HOME"
CONFIG_DIR="$HOME/.config"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Initialize output files with metadata header
{
    echo "System Configuration Backup"
    echo "System: $HOSTNAME"
    echo "OS: $OS_NAME $OS_VERSION"
    echo "Date: $TIMESTAMP"
} > "$HUMAN_READABLE"
{
    echo "---"
    echo "system_config:"
    echo "  metadata:"
    echo "    hostname: $HOSTNAME"
    echo "    os_name: $OS_NAME"
    echo "    os_version: $OS_VERSION"
    echo "    timestamp: $TIMESTAMP"
} > "$YAML_OUTPUT"

# Helper function to append to both outputs
append_output() {
    local section=$1
    local human_text=$2
    local yaml_key=$3
    local yaml_value=$4
    echo -e "\n$section\n$human_text" >> "$HUMAN_READABLE"
    echo "  $yaml_key:" >> "$YAML_OUTPUT"
    echo "$yaml_value" | sed 's/^/    /' >> "$YAML_OUTPUT"
}

# 1. Mount Points (using labels where possible)
echo "Collecting mount points..."
MOUNTS=""
while read -r line; do
    device=$(echo "$line" | awk '{print $1}')
    mountpoint=$(echo "$line" | awk '{print $2}')
    fstype=$(echo "$line" | awk '{print $3}')
    # Get label if available
    label=$(lsblk -no LABEL "$device" 2>/dev/null)
    if [ -n "$label" ]; then
        src="LABEL=$label"
    else
        src="$device"
    fi
    MOUNTS+="$src $mountpoint $fstype\n"
    echo "  - src: $src" >> "$YAML_OUTPUT"
    echo "    mountpoint: $mountpoint" >> "$YAML_OUTPUT"
    echo "    fstype: $fstype" >> "$YAML_OUTPUT"
done < <(findmnt -lo source,target,fstype | grep -vE '(/run|/sys|/proc|/dev)')
append_output "Mount Points" "$MOUNTS" "mounts" ""

# 2. Symlinks in home directory (excluding hidden directories)
echo "Collecting symlinks in $HOME_DIR (excluding hidden directories)..."
SYMLINKS=""
echo "  symlinks:" >> "$YAML_OUTPUT"
while IFS= read -r link; do
    target=$(readlink -f "$link")
    SYMLINKS+="$link -> $target\n"
    echo "    - src: $target" >> "$YAML_OUTPUT"
    echo "      dest: $link" >> "$YAML_OUTPUT"
done < <(find "$HOME_DIR" -maxdepth 3 -type l -not -path "$HOME_DIR/.*/*")
append_output "Symlinks in $HOME_DIR" "${SYMLINKS:-No symlinks found}" "symlinks" ""

# 3. Installed Packages (simplified, user-installed only)
echo "Collecting installed packages..."
if command -v dnf >/dev/null; then
    PACKAGES=$(dnf list --installed | grep -vE '^(kernel|glibc|systemd)' | awk '{print $1}' | sort)
elif command -v apt >/dev/null; then
    PACKAGES=$(apt list --installed | grep -vE '^(linux-|libc|systemd)' | cut -d'/' -f1 | sort)
else
    PACKAGES="Unable to detect package manager"
fi
append_output "Installed Packages" "$PACKAGES" "packages" "$(echo "$PACKAGES" | sed 's/^/    - /')"

# 4. GUI Applications (based on .desktop files)
echo "Collecting GUI applications..."
GUI_APPS=""
find /usr/share/applications /usr/local/share/applications "$HOME_DIR/.local/share/applications" -name "*.desktop" 2>/dev/null | while read -r desktop; do
    name=$(grep '^Name=' "$desktop" | head -1 | cut -d'=' -f2)
    [ -n "$name" ] && GUI_APPS+="$name\n"
    [ -n "$name" ] && echo "    - $name" >> "$YAML_OUTPUT"
done
append_output "GUI Applications" "$GUI_APPS" "gui_apps" ""

# 5. Running Services
echo "Collecting running services..."
SERVICES=$(systemctl list-units --type=service --state=running | grep '\.service' | awk '{print $1}')
append_output "Running Services" "$SERVICES" "services" "$(echo "$SERVICES" | sed 's/^/    - /')"

# 6. Cron Jobs
echo "Collecting cron jobs..."
CRON_JOBS=""
for user in $(cut -d: -f1 /etc/passwd); do
    crontab=$(crontab -u "$user" -l 2>/dev/null)
    if [ -n "$crontab" ]; then
        CRON_JOBS+="User $user:\n$crontab\n"
        echo "    - user: $user" >> "$YAML_OUTPUT"
        echo "      jobs:" >> "$YAML_OUTPUT"
        echo "$crontab" | while read -r line; do
            echo "        - $line" >> "$YAML_OUTPUT"
        done
    fi
done
append_output "Cron Jobs" "$CRON_JOBS" "cron_jobs" ""

# 7. Firewall Rules (simplified)
echo "Collecting firewall rules..."
FWRULES=""
if command -v firewall-cmd >/dev/null; then
    FWRULES=$(firewall-cmd --list-all)
elif command -v ufw >/dev/null; then
    FWRULES=$(ufw status)
else
    FWRULES="No firewall detected"
fi
append_output "Firewall Rules" "$FWRULES" "firewall_rules" "$(echo "$FWRULES" | sed 's/^/    /')"

# 8. User Dotfiles
echo "Collecting dotfiles..."
DOTFILES=""
find "$HOME_DIR" -maxdepth 1 -name ".*" -type f | while read -r file; do
    DOTFILES+="$file\n"
    echo "    - $file" >> "$YAML_OUTPUT"
done
append_output "User Dotfiles" "$DOTFILES" "dotfiles" ""

# 9. Application Configurations (.config subdirectories with interactive selection)
echo "Collecting application configurations from $CONFIG_DIR..."
APP_CONFIGS=""
SELECTED_CONFIGS=()

# Default configs to suggest
DEFAULT_CONFIGS=("VSCodium" "lutris" "obs-studio")

# List all .config subdirectories
if [ -d "$CONFIG_DIR" ]; then
    echo "Found the following subdirectories in $CONFIG_DIR:"
    find "$CONFIG_DIR" -maxdepth 1 -type d | while read -r dir; do
        basename=$(basename "$dir")
        [ "$basename" != ".config" ] && echo "- $basename"
    done
    echo -e "\nDefault configs to back up: ${DEFAULT_CONFIGS[*]}"
    echo "Enter configs to EXCLUDE (e.g., BraveSoftware), separated by spaces, or press Enter to use defaults:"
    read -r EXCLUDED
    EXCLUDED=($EXCLUDED)

    # Collect configs, skipping excluded ones
    echo "  app_configs:" >> "$YAML_OUTPUT"
    find "$CONFIG_DIR" -maxdepth 1 -type d | while read -r dir; do
        basename=$(basename "$dir")
        if [ "$basename" != ".config" ]; then
            skip=false
            for excl in "${EXCLUDED[@]}"; do
                if [ "$basename" = "$excl" ]; then
                    skip=true
                    break
                fi
            done
            if [ "$skip" = false ]; then
                SELECTED_CONFIGS+=("$dir")
                APP_CONFIGS+="$dir\n"
                echo "    - path: $dir" >> "$YAML_OUTPUT"
            fi
        fi
    done
else
    APP_CONFIGS="No .config directory found\n"
    echo "  app_configs: []" >> "$YAML_OUTPUT"
fi

append_output "Application Configurations" "$APP_CONFIGS" "app_configs" ""

echo "Configuration saved to $HUMAN_READABLE and $YAML_OUTPUT"
echo "Please copy the selected .config subdirectories to your playbook's '$BACKUP_DIR/files/home/user/.config/' directory for system $HOSTNAME ($OS_NAME):"
for dir in "${SELECTED_CONFIGS[@]}"; do
    echo "- $dir -> $BACKUP_DIR/files/home/user/.config/$(basename "$dir")/"
done