#!/bin/sh

## Copyright (C) 2012 - 2023 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

output_cmd="true"
#output_cmd="echo"

script_name="power-savings-disable-in-vms"

true "$script_name: INFO: Using 'return' in combination with 'exit' so this script can be both, being 'source'd as well as executed."

if test -f /usr/share/qubes/marker-vm ; then
   $output_cmd "$script_name: INFO: Not running in Qubes, not doing anything."
   return 0
   exit 0
fi

if [ ! "$XDG_SESSION_TYPE" = "tty" ]; then
   $output_cmd "$script_name: INFO: Not running in tty, not doing anything."
fi

if ! tty | grep --quiet /dev/tty ; then
   $output_cmd "$script_name: INFO: Not running in a login shell, not doing anything."
   return
   exit 0
fi

if ! command -v setterm >/dev/null ; then
   $output_cmd "$script_name: INFO: setterm not installed. Stop."
   return 0
   exit 0
fi

if command -v systemd-detect-virt >/dev/null ; then
   result="$(systemd-detect-virt)"
else
   $output_cmd "$script_name: INFO: systemd-detect-virt not executable found. Stop."
   return 0
   exit 0
fi

if [ "$result" = "" ]; then
   $output_cmd "$script_name: INFO: Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
fi

setterm -blank 0 2>/dev/null
$output_cmd "$script_name: INFO: exit code: $?"
setterm -powerdown 0 2>/dev/null
$output_cmd "$script_name: INFO: exit code: $?"

return 0
exit 0
