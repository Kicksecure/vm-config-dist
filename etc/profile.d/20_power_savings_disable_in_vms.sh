#!/bin/bash

## This file is part of Whonix.
## Copyright (C) 2012 - 2014 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

virt_what_command_exit_code="0"
command -v virt-what >/dev/null || { virt_what_command_exit_code="$?" ; true; };

if [ "$virt_what_command_exit_code" = "0" ]; then
   true "$0: virt-what found. Continue."
elif [ -x "/usr/sbin/virt-what" ]; then
   true "$0: /usr/sbin/virt-what executable. Continue."
else
   true "$0: virt-what not found. Stop."
   return 0
   exit 0
fi

setterm_command_exit_code="0"
command -v setterm >/dev/null || { setterm_command_exit_code="$?" ; true; };

if [ ! "$setterm_command_exit_code" = "0" ]; then
   true "$0: setterm not installed. Stop."
   return 0
   exit 0
else
   true "$0: setterm found. Continue."
fi

result="$(sudo virt-what)"

if [ "$result" = "" ]; then
   true "Not running in a Virtual Machine (or none detected), therefore not disabling monitor power saving. Stop."
   return 0
   exit 0
else
   true "$0: VM $result found. Continue."
fi

setterm -blank 0
setterm -powerdown 0
