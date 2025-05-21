#!/bin/sh

## Copyright (C) 2012 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## Hide all script output to prevent showing any output during a (SSH) login shell.
## For debugging, comment this line out.
## Bad idea.
#exec > /dev/null 2>&1

timeout_wrapper() {
   timeout \
      --kill-after="1" \
      "1" \
      "$@" \
      >/dev/null 2>/dev/null
}

true "$0: INFO: Using 'return' in combination with 'exit' so this script can be both, being 'source'd as well as executed."

if test -f "/usr/share/qubes/marker-vm" ; then
   true "$0: INFO: Not running in Qubes, not doing anything."
   return 0
   exit 0
fi

if command -v "systemd-detect-virt" >/dev/null 2>/dev/null ; then
   result="$(timeout_wrapper "systemd-detect-virt" 2>&1)" || true
else
   true "$0: INFO: systemd-detect-virt not executable found. Stop."
   return 0
   exit 0
fi
if [ "$result" = "" ]; then
   true "$0: INFO: Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
fi

true "$0: VM $result found. Continue."

if [ "$XDG_SESSION_TYPE" = "tty" ]; then
   if ! tty | grep -- "/dev/tty" >/dev/null 2>/dev/null ; then
      true "$0: INFO: Not running in a login shell, not doing anything."
      return
      exit 0
   fi
   if ! command -v setterm >/dev/null 2>/dev/null ; then
      true "$0: INFO: setterm not installed. Stop."
      return 0
      exit 0
   fi
   timeout_wrapper setterm -blank 0 || true
   timeout_wrapper setterm -powerdown || true
   return 0
   exit 0
fi

if [ -z "$XDG_CONFIG_DIRS" ]; then
   XDG_CONFIG_DIRS="/etc/xdg"
fi
if ! printf '%s\n' "$XDG_CONFIG_DIRS" | grep -- "/usr/share/kde-power-savings-disable-in-vms/" >/dev/null 2>/dev/null ; then
   export XDG_CONFIG_DIRS="/usr/share/kde-power-savings-disable-in-vms/:$XDG_CONFIG_DIRS"
fi

if [ "$(id -u)" = "0" ]; then
   true "$0: Can not run as root. Exiting."
   return 0
   exit 0
fi

if [ "$XDG_SESSION_TYPE" = "x11" ]; then
   if ! command -v xset >/dev/null 2>/dev/null ; then
      true "$0: xset unavailable. Exiting."
      exit 0
   fi
   timeout_wrapper xset s off || true
   timeout_wrapper xset -dpms || true
elif [ "$XDG_SESSION_TYPE" = "wayland" ]; then
   true "$0: wayland support not implemented. Exiting."
   return 0
   exit 0
fi

return 0
exit 0
