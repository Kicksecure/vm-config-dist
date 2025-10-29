#!/bin/sh

## Copyright (C) 2020 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## Automatic fallback to softwarecontext renderer
## https://www.kicksecure.com/wiki/Tuning#Renderer
##
## Useful for:
## - Monero
##   https://github.com/monero-project/monero-gui/issues/2878
##   https://github.com/monero-project/monero-gui/pull/4419
## - signal-desktop
## - maybe also wire-desktop?
##
## https://forums.whonix.org/t/video-editing-software-fails-to-launch-on-whonix-virtualbox-kvm/17241
## Causes issues for:
## - shotcut
## - kdenlive

## If 'OpenGL core profile renderer' is 'llvmpipe' according to 'eglinfo',
## then set environment variable: QMLSCENE_DEVICE=softwarecontext
## (Only if not already set to anything else.)
## Otherwise, do nothing.
##
## This means in case hardware acceleration is
## * Unavailable: Set the environment variable.
## * Available: Do nothing.

## Package 'mesa-utils' provides 'eglinfo'.

#eglinfo | grep -- "OpenGL core profile renderer" | grep -- llvmpipe
## example output:
## OpenGL core profile renderer: llvmpipe (LLVM 19.1.7, 256 bits)

if ! command -v eglinfo >/dev/null 2>/dev/null ; then
   true "$0 ERROR: eglinfo not found. Stop."
   return 0
   exit 0
fi

if eglinfo 2>/dev/null | grep -- "OpenGL core profile renderer" | grep -- llvmpipe >/dev/null 2>/dev/null; then
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

export QMLSCENE_DEVICE=softwarecontext
