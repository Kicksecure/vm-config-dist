#!/bin/sh

## Copyright (C) 2012 - 2023 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

output_cmd="true"
#output_cmd="echo"

true "$0: INFO: Using 'return' in combination with 'exit' so this script can be both, being 'source'd as well as executed."

if test -f /usr/share/qubes/marker-vm ; then
   $output_cmd "$0: INFO: Not running in Qubes, not doing anything."
   return 0
   exit 0
fi

if command -v systemd-detect-virt >/dev/null ; then
   result="$(systemd-detect-virt 2>&1)"
else
   $output_cmd "$0: INFO: systemd-detect-virt not executable found. Stop."
   return 0
   exit 0
fi
if [ "$result" = "" ]; then
   $output_cmd "$0: INFO: Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
fi

true "$0: VM $result found. Continue."

if [ "$XDG_SESSION_TYPE" = "tty" ]; then
   if ! tty | grep --quiet /dev/tty ; then
      $output_cmd "$0: INFO: Not running in a login shell, not doing anything."
      return
      exit 0
   fi
   if ! command -v setterm >/dev/null ; then
      $output_cmd "$0: INFO: setterm not installed. Stop."
      return 0
      exit 0
   fi
   setterm -blank 0 2>/dev/null
   $output_cmd "$0: INFO: exit code: $?"
   setterm -powerdown 0 2>/dev/null
   $output_cmd "$0: INFO: exit code: $?"
   return 0
   exit 0
fi

if [ -z "$XDG_CONFIG_DIRS" ]; then
   XDG_CONFIG_DIRS=/etc/xdg
fi
if ! echo "$XDG_CONFIG_DIRS" | grep --quiet /usr/share/kde-power-savings-disable-in-vms/ ; then
   export XDG_CONFIG_DIRS=/usr/share/kde-power-savings-disable-in-vms/:$XDG_CONFIG_DIRS
fi

(
   if [ "$(id -u)" = "0" ]; then
      true "$0: Can not run as root. Exiting."
      return 0
      exit 0
   fi
   sleep 60 &
   wait "$!"

   if [ "$XDG_SESSION_TYPE" = "x11" ]; then
      if ! command -v xset >/dev/null ; then
         true "$0: xset unavailable. Exiting."
         exit 0
      fi
      xset s off
      true "$0: exit code: $?"
      xset -dpms
      true "$0: exit code: $?"
   fi

   if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
      true "$0: wayland support not implemented. Exiting."
      return 0
      exit 0
   fi

   return 0
   exit 0
) &

return 0
exit 0
