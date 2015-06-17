#!/bin/bash

## This file is part of Whonix.
## Copyright (C) 2012 - 2014 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

output_cmd="true"
#output_cmd="echo"

script_name="power-savings-disable-in-vms"

true $script_name: Using "return" in combination with "exit" so this script can be both, being "source"d as well as executed.

if ! shopt -q login_shell ; then
   $output_cmd "$script_name: Not running in a login shell, not doing anything."
   return
   exit 0
fi

if ! test -x /usr/sbin/virt-what >/dev/null ; then
   $output_cmd "$script_name: /usr/sbin/virt-what not executable found. Stop."
   return 0
   exit 0
fi

if ! command -v setterm >/dev/null ; then
   $output_cmd "$script_name: setterm not installed. Stop."
   return 0
   exit 0
fi

result="$(sudo virt-what)"

if [ "$result" = "" ]; then
   $output_cmd "$script_name:Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
fi

setterm -blank 0 2>/dev/null
$output_cmd "$script_name: exit code: $?"
setterm -powerdown 0 2>/dev/null
$output_cmd "$script_name: exit code: $?"

return 0
exit 0
