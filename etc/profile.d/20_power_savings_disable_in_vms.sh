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
   true "$0: INFO: Running inside Qubes. Stop."
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

if [ "$result" = "none" ]; then
   true "$0: INFO: No virtualization detected, therefore not disabling monitor power saving. Stop."
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
   if ! tty 2>/dev/null | grep -- "/dev/tty" >/dev/null 2>/dev/null ; then
      true "$0: INFO: Not running inside tty. Stop."
      return 0
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

## GUI power management configuration is in:
## - /usr/libexec/vm-config-dist/suppress-power-management-in-vms
## - /usr/lib/systemd/system/suppress-power-management-in-vms.service

return 0
exit 0
