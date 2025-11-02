#!/usr/bin/python3 -su

# Copyright (C) 2025 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
# See the file COPYING for copying conditions.

# pylint: disable=broad-exception-caught

"""
wlr_resize_watcher.py - Watches for changes to the native display resolution
of all displays attached to all graphics cards on the system, and instructs
the Wayland compositor to change the display resolution for that display to
match. This allows dynamic resolution changes to work in VirtualBox and KVM.
"""

import sys
import re
import time
import os
import subprocess
import traceback
from pathlib import Path
from typing import Pattern, NoReturn
import pyudev  # type: ignore

drm_match_re: Pattern[str] = re.compile(r".*/drm/card\d+$")
card_match_re: Pattern[str] = re.compile(r"^card\d+$")
disp_match_re: Pattern[str] = re.compile(r"^card\d+-.*$")
whitespace_start_re: Pattern[str] = re.compile(r"^\s+")
modes_re: Pattern[str] = re.compile(r"\s+Modes:$")
current_mode_re: Pattern[str] = re.compile(r".*[( ]current[,)].*")


# pylint: disable=too-few-public-methods
class DisplayInfo:
    """
    Stores the name and resolution associated with a display.
    """

    def __init__(self, disp_name: str, disp_mode: str) -> None:
        self.disp_name = disp_name
        self.disp_mode = disp_mode


def get_udev_card_event(udev_mon: pyudev.Monitor) -> str:
    """
    Listens for udev events affecting a drm/card* device, and outputs the list
    of affected cards.
    """

    card_name: str | None = None
    for udev_dev in iter(udev_mon.poll, None):
        dev_name: str = udev_dev.sys_path
        if drm_match_re.match(dev_name):
            dev_name_parts: list[str] = dev_name.split("/")
            card_name = dev_name_parts[len(dev_name_parts) - 1]
            break
    assert card_name is not None
    return card_name


# pylint: disable=too-many-branches
def get_compositor_disp_list() -> list[DisplayInfo] | None:
    """
    Gets all displays that the compositor currently sees, along with their
    current resolution.
    """
    try:
        wlr_randr_lines: list[str] = subprocess.run(
            ["/usr/bin/wlr-randr"],
            env={
                "XDG_RUNTIME_DIR": f"{os.environ["XDG_RUNTIME_DIR"]}",
                "LC_ALL": "C",
            },
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout.split("\n")
    except Exception:
        print(
            "ERROR: Could not get list of displays from compositor!",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    if len(wlr_randr_lines) == 1 and wlr_randr_lines[0].strip() == "":
        ## Empty wlr-randr output, the compositor most likely doesn't see any
        ## displays
        return None

    out_list: list[DisplayInfo] = []
    disp_name: str | None = None
    disp_mode: str | None = None
    in_modes_zone: bool = False
    modes_zone_indent: int = 0

    for idx, line in enumerate(wlr_randr_lines):
        if idx == 0:
            if whitespace_start_re.match(line):
                print(
                    "ERROR: Unexpected whitespace on first line of "
                    "wlr-randr output! wlr-randr output:",
                    file=sys.stderr,
                )
                print(f"{"\n".join(wlr_randr_lines)}", file=sys.stderr)
                sys.exit(1)
            disp_name = line.split(" ")[0]
            continue

        if not whitespace_start_re.match(line):
            if disp_name is None or disp_mode is None:
                print(
                    "ERROR: Unable to find active display mode for "
                    "a screen in wlr-randr output! wlr-randr output:",
                    file=sys.stderr,
                )
                print(f"{"\n".join(wlr_randr_lines)}", file=sys.stderr)
                sys.exit(1)
            out_list.append(DisplayInfo(disp_name, disp_mode))
            disp_name = line.split(" ")[0]
            disp_mode = None
            in_modes_zone = False
            continue

        if modes_re.match(line):
            in_modes_zone = True
            continue

        if in_modes_zone and modes_zone_indent == 0:
            modes_zone_indent = len(line) - len(line.lstrip(" "))

        if (
            in_modes_zone
            and (len(line) - len(line.lstrip(" "))) < modes_zone_indent
        ):
            in_modes_zone = False
            modes_zone_indent = 0
            continue

        if not in_modes_zone:
            continue

        line_parts: list[str] = line.strip().split(" ", maxsplit=4)
        if len(line_parts) < 4:
            print(
                "ERROR: Too few fields in wlr-randr mode "
                "specification! wlr-randr output:",
                file=sys.stderr,
            )
            print(f"{"\n".join(wlr_randr_lines)}", file=sys.stderr)
            sys.exit(1)
        if len(line_parts) == 4:
            ## This mode specification is not the active one for the
            ## current display, skip it
            continue
        if current_mode_re.match(line_parts[4]):
            disp_mode = line_parts[0]

    return out_list


def get_hw_disp_list(card_list: list[str]) -> list[DisplayInfo] | None:
    """
    Gets all recognized displays present on the specified list of graphics
    cards, and their native resolution.
    """

    out_list: list[DisplayInfo] = []

    for card in card_list:
        try:
            card_path: Path = Path(f"/sys/class/drm/{card}")
            disp_list: list[str] = [
                x.name
                for x in card_path.iterdir()
                if x.is_dir() and disp_match_re.match(x.name)
            ]
        except FileNotFoundError:
            ## This will happen if the card no longer exists. We don't
            ## explicitly check for existence first to avoid a TOCTOU.
            continue
        except Exception:
            print(
                "ERROR: Cannot enumerate displays from a graphics card!",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

        for display in disp_list:
            display_name_list: list[str] = display.split("-", maxsplit=1)
            if len(display_name_list) != 2:
                print(
                    f"ERROR: Bug in parsing display ID '{display}'!",
                    file=sys.stderr,
                )
                sys.exit(1)
            display_name = display_name_list[1]

            try:
                display_modes_path: Path = Path(
                    f"/sys/class/drm/{card}/{display}/modes"
                )
                display_modes_lines: list[str] = (
                    display_modes_path.read_text(encoding="utf-8")
                    .strip()
                    .split("\n")
                )
                if (
                    len(display_modes_lines) == 1
                    and display_modes_lines[0] == ""
                ):
                    ## Display isn't connected, skip it
                    continue
                display_mode: str = display_modes_lines[0]
                out_list.append(DisplayInfo(display_name, display_mode))
            except FileNotFoundError:
                ## Same rationale as for card enumeration, see above
                continue
            except Exception:
                print(
                    "ERROR: Cannot read mode information for a display!",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)

    if len(out_list) == 0:
        return None
    return out_list


def sync_hw_resolution_with_compositor(card_name: str | None) -> None:
    """
    Sets the compositor's display resolution for all displays on all specified
    graphics cards to the native resolution.
    """

    real_card_list: list[str]
    if card_name is None:
        ## Manually discover all available cards from /sys/class/drm.
        drm_path: Path = Path("/sys/class/drm")
        if not drm_path.is_dir():
            print(
                "ERROR: /sys/class/drm does not exist or is not a "
                "directory!",
                file=sys.stderr,
            )
            sys.exit(1)
        real_card_list = [
            x.name
            for x in drm_path.iterdir()
            if x.is_dir() and card_match_re.match(x.name)
        ]
    else:
        real_card_list = [card_name]

    compositor_disp_list: list[DisplayInfo] | None = get_compositor_disp_list()
    if compositor_disp_list is None:
        return

    hw_disp_list: list[DisplayInfo] | None = get_hw_disp_list(real_card_list)
    if hw_disp_list is None:
        return

    for hw_display in hw_disp_list:
        matched_compositor_display: DisplayInfo | None = None
        for compositor_display in compositor_disp_list:
            if compositor_display.disp_name == hw_display.disp_name:
                matched_compositor_display = compositor_display
                break
        if matched_compositor_display is None:
            continue
        if hw_display.disp_mode != matched_compositor_display.disp_mode:
            try:
                subprocess.run(
                    [
                        "/usr/bin/wlr-randr",
                        "--output",
                        hw_display.disp_name,
                        "--custom-mode",
                        f"{hw_display.disp_mode}@60",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                print(
                    "WARNING: Unable to sync display resolution for display "
                    f"'{hw_display.disp_name}'!",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)


def executable_exists_and_is_running(exe_name: str) -> int:
    """
    Checks if the specified executable exists and is actively running. Note
    that this will give a false negative if an executable was executed from a
    relative path when an absolute path was provided, or vice versa. It may
    also fail if the executable name contains characters that pgrep considers
    part of a regex, thus it should not be run with untrusted input.

    Returns 0 on success, 1 if the executable is missing, 2 if the executable
    is not running.
    """

    if not Path(exe_name).is_file():
        return 1
    if not subprocess.run(
        ["/usr/bin/pgrep", "-f", f"^{exe_name}( |$)"],
        check=False,
        capture_output=True,
    ).returncode == 0:
        return 2
    return 0


def set_all_displays_resolution_to_default() -> None:
    """
    Sets the screen resolution of all displays to a default (hardcoded) value,
    currently 1920x1080.
    """

    disp_list: list[DisplayInfo] | None = get_compositor_disp_list()
    hardcoded_res: str = "1920x1080"

    if disp_list is None:
        return
    for disp in disp_list:
        try:
            subprocess.run(
                [
                    "/usr/bin/wlr-randr",
                    "--output",
                    disp.disp_name,
                    "--custom-mode",
                    f"{hardcoded_res}@60",
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print(
                "WARNING: Unable to set default display resolution for "
                f"display '{disp.disp_name}'!",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)


# pylint: disable=too-many-return-statements
def check_virtualizer_helpers() -> bool:
    """
    Displays an error message and returns False if a needed virtualizer helper
    is not detected.
    """

    try:
        virtualizer_str: str = subprocess.run(
            ["/usr/bin/systemd-detect-virt"],
            check=False,
            capture_output=True,
            encoding="utf-8",
        ).stdout.strip()
        if virtualizer_str == "oracle":
            found_drm_client: int = executable_exists_and_is_running(
                "/usr/bin/VBoxDRMClient"
            )
            if found_drm_client == 1:
                print(
                    "WARNING: VBoxDRMClient is missing!",
                    file=sys.stderr,
                )
                return False
            if found_drm_client == 2:
                print(
                    "WARNING: VBoxDRMClient is not running!",
                    file=sys.stderr,
                )
                return False

        elif virtualizer_str == "kvm":
            found_spice_vdagentd: int = executable_exists_and_is_running(
                "/usr/bin/spice-vdagentd"
            )
            if found_spice_vdagentd == 1:
                print(
                    "WARNING: spice-vdagentd is missing!",
                    file=sys.stderr,
                )
                return False
            if found_spice_vdagentd == 2:
                print(
                    "WARNING: spice-vdagentd is not running!",
                    file=sys.stderr,
                )
                return False

        elif virtualizer_str == "none":
            print(
                "INFO: Running on physical hardware, exiting.",
                file=sys.stderr,
            )
            sys.exit(0)

        else:
            print(
                "WARNING: Running on an unsupported virtualizer!",
                file=sys.stderr,
            )
            return False

    except Exception:
        print(
            "WARNING: Cannot detect virtualizer in use!",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return False

    return True


def main() -> NoReturn:
    """
    Main function.
    """

    if Path("/usr/share/qubes/marker-vm").is_file():
        print("INFO: Qubes OS detected, exiting.", file=sys.stderr)
        sys.exit(0)

    ## The method we use for detecting display resolution changes is as
    ## follows:
    ##
    ## - Listen for udev events for all DRM cards on the system.
    ## - Every time an event is received for a card, wait half a second so
    ##   that the compositor has time to register any new displays that may
    ##   have appeared.
    ## - Enumerate all displays seen by the compositor.
    ## - Enumerate all displays supported by the card.
    ## - Determine the native display resolution of all displays on the card.
    ## - For all displays seen by the compositor, whose current resolution
    ##   does not match the native resolution, change the resolution used by
    ##   the compositor to match.
    ##
    ## The udev listening and sleep are done here, most of the rest of the
    ## logic is in sync_hw_resolution_with_compositor().
    ##
    ## Note that we always assume that the desired display frequency is 60 Hz.
    ## This may not always hold true for physical screens, but should be fine
    ## for virtual displays.

    ## If we can't find an active virtualizer helper, set all displays to a
    ## comfortable default display resolution.
    if not check_virtualizer_helpers():
        set_all_displays_resolution_to_default()
    else:
        sync_hw_resolution_with_compositor(None)

    try:
        udev_ctx: pyudev.Context = pyudev.Context()
        udev_mon: pyudev.Monitor = pyudev.Monitor.from_netlink(udev_ctx)
        udev_mon.filter_by("drm")
    except Exception:
        print(
            "ERROR: Cannot listen for DRM udev events!",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    while True:
        mod_card: str = get_udev_card_event(udev_mon)
        time.sleep(0.5)
        sync_hw_resolution_with_compositor(mod_card)

if __name__ == "__main__":
    main()
