#!/bin/sh

## Copyright (C) 2017 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

if test -f "/usr/share/qubes/marker-vm" ; then
   true "$0: INFO: Running inside Qubes. Stop."
   return 0
   exit 0
fi

if [ "$XDG_SESSION_TYPE" = "tty" ]; then
   true "$0: INFO: Running inside tty. Stop."
   return 0
   exit 0
fi

if tty 2>/dev/null | grep -- "/dev/tty" >/dev/null 2>/dev/null ; then
   true "$0: INFO: Running inside tty. Stop."
   return 0
   exit 0
fi

if command -v "systemd-detect-virt" >/dev/null 2>/dev/null ; then
   result="$("systemd-detect-virt" 2>&1)" || true
else
   true "$0: INFO: systemd-detect-virt not found. Stop."
   return 0
   exit 0
fi

if [ "$result" = "none" ]; then
   true "$0: INFO: No virtualization detected, therefore not disabling kde screen saver. Stop."
   return 0
   exit 0
fi
if [ "$result" = "" ]; then
   true "$0: INFO: Not running in a Virtual Machine (or none detected), therefore not disabling kde screen saver. Stop."
   return 0
   exit 0
fi

true "$0: INFO: VM $result found. Continue."

if [ -z "$XDG_CONFIG_DIRS" ]; then
   XDG_CONFIG_DIRS="/etc/xdg"
fi

if ! printf '%s\n' "$XDG_CONFIG_DIRS" | grep -- "/usr/share/kde-screen-locker-disable-in-vms/" >/dev/null 2>/dev/null ; then
   export XDG_CONFIG_DIRS="/usr/share/kde-screen-locker-disable-in-vms/:$XDG_CONFIG_DIRS"
fi
