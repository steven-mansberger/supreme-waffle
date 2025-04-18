#!/bin/bash

# Gather system metadata
HOSTNAME=$(hostname | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
OS_NAME=$(grep '^NAME=' /etc/os-release | cut -d'"' -f2 | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
OS_VERSION=$(grep '^VERSION_ID=' /etc/os-release | cut -d'=' -f2 | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')
TIMESTAMP=$(date '+%Y-%m-%dT%H-%M-%S')
CURRENT_USER=$(whoami)

# Output directory and files with system-specific names and timestamp
BACKUP_DIR="backups/$HOSTNAME/$TIMESTAMP"
HUMAN_READABLE="$BACKUP_DIR/system_config_${HOSTNAME}_${OS_NAME}.txt"
YAML_OUTPUT="$BACKUP_DIR/system_config_${HOSTNAME}_${OS_NAME}.yml"
CRONTABS_DIR="$BACKUP_DIR/crontabs"
COMMANDS_DIR="$BACKUP_DIR/commands"
HOME_DIR="$HOME"

# Create backup directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$CRONTABS_DIR"
mkdir -p "$COMMANDS_DIR"

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
    echo "" >> "$YAML_OUTPUT"  # Consistent newline before section
    echo "  $yaml_key:" >> "$YAML_OUTPUT"
    echo -e "$yaml_value" | sed 's/^/    /' >> "$YAML_OUTPUT"
}

# 1. Mount Points (from fstab and findmnt)
echo "Collecting mount points..."
MOUNTS=""
MOUNTS_YAML=""
declare -A MOUNT_SEEN

# Parse /etc/fstab
while read -r device mountpoint fstype options dump pass; do
    # Skip comments, empty lines, or invalid entries
    [[ "$device" =~ ^# ]] || [[ -z "$device" ]] || [[ "$mountpoint" == "none" ]] && continue
    # Skip non-filesystem mounts
    [[ "$fstype" == "swap" ]] || [[ "$fstype" == "proc" ]] || [[ "$fstype" == "sysfs" ]] || [[ "$fstype" == "tmpfs" ]] && continue
    # Use label if available
    label=$(lsblk -no LABEL "$device" 2>/dev/null)
    src=${label:+LABEL=$label}
    src=${src:-$device}
    key="$src $mountpoint $fstype"
    if [[ -z "${MOUNT_SEEN[$key]}" ]]; then
        MOUNTS+="$src $mountpoint $fstype\n"
        MOUNTS_YAML+="- src: $src\n  mountpoint: $mountpoint\n  fstype: $fstype\n"
        MOUNT_SEEN[$key]=1
    fi
done < <(grep -v '^\s*#' /etc/fstab | grep -v '^\s*$')

# Add active mounts from findmnt
while read -r line; do
    device=$(echo "$line" | awk '{print $1}')
    mountpoint=$(echo "$line" | awk '{print $2}')
    fstype=$(echo "$line" | awk '{print $3}')
    # Skip volatile or system mounts
    [[ "$mountpoint" =~ ^(/run|/sys|/proc|/dev) ]] && continue
    label=$(lsblk -no LABEL "$device" 2>/dev/null)
    src=${label:+LABEL=$label}
    src=${src:-$device}
    key="$src $mountpoint $fstype"
    if [[ -z "${MOUNT_SEEN[$key]}" ]]; then
        MOUNTS+="$src $mountpoint $fstype\n"
        MOUNTS_YAML+="- src: $src\n  mountpoint: $mountpoint\n  fstype: $fstype\n"
        MOUNT_SEEN[$key]=1
    fi
done < <(findmnt -lo source,target,fstype)
append_output "Mount Points" "${MOUNTS:-No mount points found}" "mounts" "${MOUNTS_YAML:-[]}"

# 2. Symlinks in home directory (excluding hidden directories)
echo "Collecting symlinks in $HOME_DIR (excluding hidden directories)..."
SYMLINKS=""
SYMLINKS_YAML=""
while IFS= read -r link; do
    target=$(readlink -f "$link")
    SYMLINKS+="$link -> $target\n"
    SYMLINKS_YAML+="- src: $target\n  dest: $link\n"
done < <(find "$HOME_DIR" -maxdepth 3 -type l -not -path "$HOME_DIR/.*/*")
append_output "Symlinks in $HOME_DIR" "${SYMLINKS:-No symlinks found}" "symlinks" "${SYMLINKS_YAML:-[]}"

# 3. Installed Packages (simplified, user-installed only)
echo "Collecting installed packages..."
PACKAGES=""
PACKAGES_YAML=""
if command -v dnf >/dev/null; then
    PACKAGES=$(dnf list --installed | grep -vE '^(kernel|glibc|systemd)' | awk '{print $1}' | sort)
    PACKAGES_YAML=$(echo "$PACKAGES" | sed 's/^/  - /')
elif command -v apt >/dev/null; then
    PACKAGES=$(apt list --installed | grep -vE '^(linux-|libc|systemd)' | cut -d'/' -f1 | sort)
    PACKAGES_YAML=$(echo "$PACKAGES" | sed 's/^/  - /')
else
    PACKAGES="Unable to detect package manager"
    PACKAGES_YAML="[]"
fi
append_output "Installed Packages" "${PACKAGES:-No packages found}" "packages" "${PACKAGES_YAML:-[]}"

# 4. GUI Applications (based on .desktop files)
echo "Collecting GUI applications..."
GUI_APPS=""
GUI_APPS_YAML=""
find /usr/share/applications /usr/local/share/applications "$HOME_DIR/.local/share/applications" -name "*.desktop" -readable 2>/dev/null | sort | while read -r desktop; do
    name=$(grep -m1 '^Name=' "$desktop" | cut -d'=' -f2-)
    if [ -n "$name" ]; then
        GUI_APPS+="$name\n"
        GUI_APPS_YAML+="  - $name\n"
    fi
done
append_output "GUI Applications" "${GUI_APPS:-No GUI applications found}" "gui_apps" "${GUI_APPS_YAML:-[]}"

# 5. Running Services
echo "Collecting running services..."
SERVICES=$(systemctl list-units --type=service --state=running | grep '\.service' | awk '{print $1}' | sort)
SERVICES_YAML=$(echo "$SERVICES" | sed 's/^/  - /')
append_output "Running Services" "${SERVICES:-No services found}" "services" "${SERVICES_YAML:-[]}"

# 6. Cron Jobs
echo "Collecting cron jobs..."
CRON_JOBS=""
CRON_JOBS_YAML=""
mkdir -p "$CRONTABS_DIR"
crontab_file="$CRONTABS_DIR/$CURRENT_USER.crontab"
if crontab -l 2>/dev/null > "$crontab_file"; then
    if [ -s "$crontab_file" ]; then
        CRON_JOBS+="User $CURRENT_USER:\n$(cat "$crontab_file")\n"
        CRON_JOBS_YAML+="- user: $CURRENT_USER\n  file: crontabs/$CURRENT_USER.crontab\n"
    else
        rm "$crontab_file"
    fi
fi
if [ "$(id -u)" -eq 0 ]; then
    for user in $(cut -d: -f1 /etc/passwd); do
        if [ "$user" != "$CURRENT_USER" ]; then
            crontab_file="$CRONTABS_DIR/$user.crontab"
            if crontab -u "$user" -l 2>/dev/null > "$crontab_file"; then
                if [ -s "$crontab_file" ]; then
                    CRON_JOBS+="User $user:\n$(cat "$crontab_file")\n"
                    CRON_JOBS_YAML+="- user: $user\n  file: crontabs/$user.crontab\n"
                else
                    rm "$crontab_file"
                fi
            fi
        fi
    done
fi
append_output "Cron Jobs" "${CRON_JOBS:-No cron jobs found}" "cron_jobs" "${CRON_JOBS_YAML:-[]}"

# 7. Firewall Rules (simplified)
echo "Collecting firewall rules..."
FWRULES=""
FWRULES_YAML=""
if command -v firewall-cmd >/dev/null; then
    FWRULES=$(firewall-cmd --list-all)
    FWRULES_YAML=$(echo "$FWRULES" | sed 's/^/    /')
elif command -v ufw >/dev/null; then
    FWRULES=$(ufw status)
    FWRULES_YAML=$(echo "$FWRULES" | sed 's/^/    /')
else
    FWRULES="No firewall detected"
    FWRULES_YAML="[]"
fi
append_output "Firewall Rules" "${FWRULES:-No firewall rules found}" "firewall_rules" "${FWRULES_YAML:-[]}"

# 8. User Dotfiles
echo "Collecting dotfiles..."
DOTFILES=""
DOTFILES_YAML=""
find "$HOME_DIR" -maxdepth 1 -name ".*" -type f -readable 2>/dev/null | sort | while read -r file; do
    DOTFILES+="$file\n"
    DOTFILES_YAML+="  - $file\n"
done
append_output "User Dotfiles" "${DOTFILES:-No dotfiles found}" "dotfiles" "${DOTFILES_YAML:-[]}"

# 9. Command Outputs
echo "Collecting command outputs..."
COMMAND_OUTPUTS=""
COMMAND_OUTPUTS_YAML=""
declare -a COMMANDS=(
    "mount:mount.txt"
    "lsblk:lsblk.txt"
    "ip a:ip_a.txt"
    "cat /etc/fstab:fstab.txt"
    "uname -a:uname_a.txt"
    "cat /etc/os-release:os_release.txt"
    "pvs:pvs.txt"
    "vgs:vgs.txt"
    "lvs:lvs.txt"
    "blkid:blkid.txt"
    "cat /etc/hosts:hosts.txt"
    "cat /etc/resolv.conf:resolv_conf.txt"
    "systemctl list-unit-files --state=enabled:enabled_services.txt"
    "cat /etc/network/interfaces:network_interfaces.txt"
    "lsmod:lsmod.txt"
    "zfs list:zfs_list.txt"
    "btrfs subvolume list /:btrfs_subvol.txt"
    "mdadm --detail --scan:mdadm_detail.txt"
    "cat /proc/mdstat:mdstat.txt"
    "getent passwd:passwd.txt"
    "getent group:group.txt"
)

# Commands requiring root
ROOT_COMMANDS=(
    "parted -l:parted_l.txt"
    "fdisk -l:fdisk_l.txt"
    "dmidecode -t system:dmidecode_system.txt"
    "iptables -L -v -n:iptables_l.txt"
    "nft list ruleset:nft_ruleset.txt"
)

for cmd_entry in "${COMMANDS[@]}"; do
    cmd=${cmd_entry%%:*}
    file=${cmd_entry##*:}
    output_file="$COMMANDS_DIR/$file"
    echo "Running: $cmd > $output_file"
    if bash -c "$cmd" > "$output_file" 2>/dev/null; then
        if [ -s "$output_file" ]; then
            COMMAND_OUTPUTS+="$cmd: commands/$file\n"
            COMMAND_OUTPUTS_YAML+="- command: $cmd\n  file: commands/$file\n"
        else
            rm "$output_file"
        fi
    else
        echo "Warning: Failed to run '$cmd'; skipping"
        rm -f "$output_file"
    fi
done

if [ "$(id -u)" -eq 0 ]; then
    for cmd_entry in "${ROOT_COMMANDS[@]}"; do
        cmd=${cmd_entry%%:*}
        file=${cmd_entry##*:}
        output_file="$COMMANDS_DIR/$file"
        echo "Running (as root): $cmd > $output_file"
        if bash -c "$cmd" > "$output_file" 2>/dev/null; then
            if [ -s "$output_file" ]; then
                COMMAND_OUTPUTS+="$cmd: commands/$file\n"
                COMMAND_OUTPUTS_YAML+="- command: $cmd\n  file: commands/$file\n"
            else
                rm "$output_file"
            fi
        else
            echo "Warning: Failed to run '$cmd'; skipping"
            rm -f "$output_file"
        fi
    done
else
    echo "Warning: Skipping root-only commands (e.g., parted, fdisk, dmidecode) as script is not run as root"
fi
append_output "Command Outputs" "${COMMAND_OUTPUTS:-No command outputs captured}" "command_outputs" "${COMMAND_OUTPUTS_YAML:-[]}"

echo "Configuration saved to $HUMAN_READABLE and $YAML_OUTPUT"
echo "Crontab files saved to $CRONTABS_DIR/"
echo "Command outputs saved to $COMMANDS_DIR/"
echo "Commit the backup to your Git repository:"
echo "  git add backups/$HOSTNAME/"
echo "  git commit -m 'Backup for $HOSTNAME on $TIMESTAMP'"
echo "  git push"