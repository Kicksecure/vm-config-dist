#!/bin/sh

## Copyright (C) 2020 - 2023 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

if command -v systemd-detect-virt >/dev/null ; then
   result="$(systemd-detect-virt)"
   ## result example:
   ## oracle
else
   echo "$0 ERROR: systemd-detect-virt not found. Stop."
   return 0
   exit 0
fi

if [ "$result" = "oracle" ]; then
   software_rendering_use=true
fi

if [ "$result" = "kvm" ]; then
   software_rendering_use=true
fi

if [ "$result" = "xen" ]; then
   software_rendering_use=true
fi

if [ ! "$software_rendering_use" = "true" ]; then
   true "$0 INFO: software_rendering_use is not set to true. Stop."
   return 0
   exit 0
fi

if [ ! "$QMLSCENE_DEVICE" = "" ]; then
   true "$0 INFO: QMLSCENE_DEVICE is already set to '$QMLSCENE_DEVICE'. Not changing. Stop."
   return 0
   exit 0
fi

## useful for:
## - signal-desktop
## - maybe also wire-desktop?
##
## Automatic fallback to softwarecontext renderer
##
## Not great to set this unconditionally in VirtualBox but there is no known
## tool which can find out from inside the VM if VirtualBox 3D acceleration
## is enabled from inside the VM, see:
## Test command from inside VM to detect if VirtualBox 3D acceleration is enabled or disabled?
## https://forums.virtualbox.org/viewtopic.php?f=3&t=97983
##
## https://forums.whonix.org/t/video-editing-software-fails-to-launch-on-whonix-virtualbox-kvm/17241
## Causes issues for:
## - shotcut
## - kdenlive
export QMLSCENE_DEVICE=softwarecontext
