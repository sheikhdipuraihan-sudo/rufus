#!/bin/bash
# Launcher script to request root privileges via GUI, preserving the
# display/auth environment so the Tk window can actually open as root.
set -e

TARGET=/opt/rufus-linux/usr/bin/rufus_linux.py

if [ "$EUID" -ne 0 ]; then
    if command -v pkexec &> /dev/null; then
        exec pkexec env \
            DISPLAY="$DISPLAY" \
            XAUTHORITY="$XAUTHORITY" \
            WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
            XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
            python3 "$TARGET"
    elif command -v gksudo &> /dev/null; then
        exec gksudo python3 "$TARGET"
    else
        zenity --error --text="Error: No GUI sudo tool found (pkexec or gksudo required)." 2>/dev/null || \
            echo "Error: No GUI sudo tool found (pkexec or gksudo required)." >&2
        exit 1
    fi
else
    exec python3 "$TARGET"
fi
