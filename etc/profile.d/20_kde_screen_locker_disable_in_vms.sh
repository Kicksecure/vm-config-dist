#!/bin/sh

## Copyright (C) 2017 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

if test -f /usr/share/qubes/marker-vm ; then
   true "$0: INFO: Not running in Qubes, not doing anything."
   return 0
   exit 0
fi

if [ "$XDG_SESSION_TYPE" = "tty" ]; then
   true "$0: INFO: Running inside tty. Stop."
   return 0
   exit 0
fi

if command -v systemd-detect-virt >/dev/null ; then
   result="$(systemd-detect-virt 2>&1)"
else
   true "$0: INFO: systemd-detect-virt not found. Stop."
   return 0
   exit 0
fi

if [ "$result" = "" ]; then
   true "$0: INFO: Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
fi

true "$0: INFO: VM $result found. Continue."

if [ -z "$XDG_CONFIG_DIRS" ]; then
   XDG_CONFIG_DIRS=/etc/xdg
fi
if ! echo "$XDG_CONFIG_DIRS" | grep --quiet /usr/share/kde-screen-locker-disable-in-vms/ ; then
   export XDG_CONFIG_DIRS=/usr/share/kde-screen-locker-disable-in-vms/:$XDG_CONFIG_DIRS
fi
