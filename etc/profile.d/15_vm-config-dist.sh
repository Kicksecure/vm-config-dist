#!/bin/sh

## Copyright (C) 2025 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

if [ -z "$XDG_CONFIG_DIRS" ]; then
  XDG_CONFIG_DIRS="/etc:/etc/xdg:/usr/share"
  export XDG_CONFIG_DIRS
fi
if [ -z "$XDG_DATA_DIRS" ]; then
  XDG_DATA_DIRS="/usr/local/share/:/usr/share/"
  export XDG_DATA_DIRS
fi

if ! printf '%s\n' "$XDG_CONFIG_DIRS" | grep -- "/usr/share/vm-config-dist" >/dev/null 2>/dev/null; then
  export XDG_CONFIG_DIRS="/usr/share/vm-config-dist/:$XDG_CONFIG_DIRS"
fi
