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
from typing import Pattern, NoReturn, Any

import pyudev  # type: ignore
import schema  # type: ignore
from strict_config_parser import strict_config_parser


# pylint: disable=too-few-public-methods
class GlobalData:
    """
    Global variables for wlr_resize_watcher.
    """

    drm_match_re: Pattern[str] = re.compile(r".*/drm/card\d+$")
    card_match_re: Pattern[str] = re.compile(r"^card\d+$")
    disp_match_re: Pattern[str] = re.compile(r"^card\d+-.*$")
    whitespace_start_re: Pattern[str] = re.compile(r"^\s+")
    modes_re: Pattern[str] = re.compile(r"\s+Modes:$")
    current_mode_re: Pattern[str] = re.compile(r".*[( ]current[,)].*")
    virtualizer_str: str | None = ""
    resize_helper_present: bool = False
    in_sysmaint_mode: bool = False

    enable_dynamic_resolution: bool = False
    warn_on_dynamic_resolution_refuse: bool = False
    standard_default_resolution: str = ""
    small_default_resolution: str = ""
    normal_wait_proc_list: list[str] = []
    sysmaint_wait_proc_list: list[str] = []
    wait_proc_timeout: int = 0

    conf_dir_list: list[str] = [
        "/etc/wlr_resize_watcher.d",
        "/usr/local/etc/wlr_resize_watcher.d",
    ]
    conf_schema: schema.Schema = schema.Schema(
        {
            "enable_dynamic_resolution": bool,
            "warn_on_dynamic_resolution_refuse": bool,
            "standard_default_resolution": schema.And(
                str,
                lambda s: re.match(r"\d+x\d+", s),
            ),
            "small_default_resolution": schema.And(
                str,
                lambda s: re.match(r"\d+x\d+", s),
            ),
            "normal_wait_proc_list": [str],
            "sysmaint_wait_proc_list": [str],
            "wait_proc_timeout": int,
        },
    )
    conf_defaults: dict[str, Any] = {
        "enable_dynamic_resolution": True,
        "warn_on_dynamic_resolution_refuse": True,
        "standard_default_resolution": "1920x1080",
        ## labwc encounters memory allocation issues when running at 1920x1080
        ## resolution under Xen's default VGA emulation. It works well at
        ## 1024x768.
        "small_default_resolution": "1024x768",
        ## No defaults are specified for 'normal_wait_proc_list' and
        ## 'sysmaint_wait_proc_list', since they would end up being added to
        ## the start of the respective lists before configured process names,
        ## rather than being overridden.
        "wait_proc_timeout": 10,
    }


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
        if GlobalData.drm_match_re.match(dev_name):
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
            if GlobalData.whitespace_start_re.match(line):
                print(
                    "ERROR: Unexpected whitespace on first line of "
                    "wlr-randr output! wlr-randr output:",
                    file=sys.stderr,
                )
                print(f"{"\n".join(wlr_randr_lines)}", file=sys.stderr)
                sys.exit(1)
            disp_name = line.split(" ")[0]
            continue

        if not GlobalData.whitespace_start_re.match(line):
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

        if GlobalData.modes_re.match(line):
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
        if GlobalData.current_mode_re.match(line_parts[4]):
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
                if x.is_dir() and GlobalData.disp_match_re.match(x.name)
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

    print(f"INFO: sync_hw_resolution_with_compositor start (card_name={card_name!r})", file=sys.stderr)

    ## Optionally send a notification and exit if dynamic resolution has
    ## been disabled.
    if not GlobalData.enable_dynamic_resolution:
        print("INFO: Dynamic resolution disabled by config. Skipping sync.", file=sys.stderr)
        if GlobalData.warn_on_dynamic_resolution_refuse:
            GlobalData.warn_on_dynamic_resolution_refuse = False
            print("INFO: warn_on_dynamic_resolution_refuse=1 -> sending notify and disabling further warnings.", file=sys.stderr)
            subprocess.run(
                [
                    "/usr/bin/notify-send",
                    "--app-name=wlr_resize_watcher",
                    "Not resizing display!",
                    "Dynamic resolution is disabled to enhance anonymity. If "
                    "you want to enable it, open the System Maintenance "
                    "Panel and click 'Configure Dynamic Resolution'.",
                ],
                check=False,
            )
        return

    real_card_list: list[str]
    if card_name is None:
        ## Manually discover all available cards from /sys/class/drm.
        print("INFO: card_name=None -> discovering cards in /sys/class/drm", file=sys.stderr)
        drm_path: Path = Path("/sys/class/drm")
        if not drm_path.is_dir():
            print("ERROR: /sys/class/drm does not exist or is not a directory!", file=sys.stderr)
            sys.exit(1)
        real_card_list = [
            x.name
            for x in drm_path.iterdir()
            if x.is_dir() and GlobalData.card_match_re.match(x.name)
        ]
        print(f"INFO: discovered cards: {real_card_list!r}", file=sys.stderr)
    else:
        real_card_list = [card_name]
        print(f"INFO: card_name provided -> using cards: {real_card_list!r}", file=sys.stderr)

    compositor_disp_list: list[DisplayInfo] | None = get_compositor_disp_list()
    if compositor_disp_list is None:
        print("INFO: compositor_disp_list=None (compositor likely sees no displays) -> returning", file=sys.stderr)
        return
    print(f"INFO: compositor reports {len(compositor_disp_list)} display(s): {[(d.disp_name, d.disp_mode) for d in compositor_disp_list]!r}", file=sys.stderr)

    hw_disp_list: list[DisplayInfo] | None = get_hw_disp_list(real_card_list)
    if hw_disp_list is None:
        print(f"INFO: hw_disp_list=None (no connected displays found for cards {real_card_list!r}) -> returning", file=sys.stderr)
        return
    print(f"INFO: hardware reports {len(hw_disp_list)} display(s): {[(d.disp_name, d.disp_mode) for d in hw_disp_list]!r}", file=sys.stderr)

    for hw_display in hw_disp_list:
        print(f"INFO: checking hw display '{hw_display.disp_name}' native_mode='{hw_display.disp_mode}'", file=sys.stderr)
        matched_compositor_display: DisplayInfo | None = None
        for compositor_display in compositor_disp_list:
            if compositor_display.disp_name == hw_display.disp_name:
                matched_compositor_display = compositor_display
                break
        if matched_compositor_display is None:
            print(f"INFO: no compositor match for hw display '{hw_display.disp_name}', skipping", file=sys.stderr)
            continue
        print(f"INFO: matched compositor display '{matched_compositor_display.disp_name}' current_mode='{matched_compositor_display.disp_mode}'", file=sys.stderr)

        if hw_display.disp_mode != matched_compositor_display.disp_mode:
            print(f"INFO: mode mismatch -> attempting sync: '{hw_display.disp_name}' {matched_compositor_display.disp_mode} -> {hw_display.disp_mode}", file=sys.stderr)
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
                print(f"INFO: synced display '{hw_display.disp_name}' to '{hw_display.disp_mode}@60'", file=sys.stderr)
            except subprocess.CalledProcessError:
                print(f"WARNING: Unable to sync display resolution for display '{hw_display.disp_name}'!", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
        else:
            print(f"INFO: display '{hw_display.disp_name}' already matches native mode '{hw_display.disp_mode}', no action needed", file=sys.stderr)

    print("INFO: sync_hw_resolution_with_compositor end", file=sys.stderr)


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
    Sets the screen resolution of all displays to a default (hardcoded) value
    appropriate for the virtualizer.
    """

    disp_list: list[DisplayInfo] | None = get_compositor_disp_list()
    selected_res: str
    if GlobalData.virtualizer_str == "xen":
        selected_res = GlobalData.small_default_resolution
    else:
        selected_res = GlobalData.standard_default_resolution

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
                    f"{selected_res}@60",
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
def check_virtualizer_type() -> None:
    """
    Records the currently-in-use virtualizer in a global variable and checks
    to see if a display resize helper is present and running.
    """

    try:
        GlobalData.virtualizer_str = subprocess.run(
            ["/usr/bin/systemd-detect-virt"],
            check=False,
            capture_output=True,
            encoding="utf-8",
        ).stdout.strip()
        if GlobalData.virtualizer_str == "oracle":
            found_drm_client: int = executable_exists_and_is_running(
                "/usr/bin/VBoxDRMClient"
            )
            if found_drm_client == 1:
                print(
                    "WARNING: VBoxDRMClient is missing!",
                    file=sys.stderr,
                )
                return
            if found_drm_client == 2:
                print(
                    "WARNING: VBoxDRMClient is not running!",
                    file=sys.stderr,
                )
                return

        elif GlobalData.virtualizer_str == "kvm":
            found_spice_vdagentd: int = executable_exists_and_is_running(
                "/usr/sbin/spice-vdagentd"
            )
            if found_spice_vdagentd == 1:
                print(
                    "WARNING: spice-vdagentd is missing!",
                    file=sys.stderr,
                )
                return
            if found_spice_vdagentd == 2:
                print(
                    "WARNING: spice-vdagentd is not running!",
                    file=sys.stderr,
                )
                return

        elif GlobalData.virtualizer_str == "xen":
            ## Xen has no virtualizer helper.
            return

        elif GlobalData.virtualizer_str == "none":
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
            return

    except Exception:
        print(
            "WARNING: Cannot detect virtualizer in use!",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return

    GlobalData.resize_helper_present = True


def check_sysmaint_mode() -> None:
    """
    Detects if the system is running in sysmaint mode or not.
    """

    proc_cmdline_file_list: list[Path] = [
        Path("/proc/cmdline"),
        Path("/proc/1/cmdline"),
    ]
    chosen_proc_cmdline_file: str | None = None

    for proc_cmdline_file in proc_cmdline_file_list:
        if proc_cmdline_file.is_file():
            chosen_proc_cmdline_file = str(proc_cmdline_file)
            break

    if chosen_proc_cmdline_file is None:
        print(
            "ERROR: Cannot find the kernel command line file!",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(
            chosen_proc_cmdline_file, "r", encoding="utf-8"
        ) as kernel_cmdline_file:
            kernel_cmdline: str = kernel_cmdline_file.read()
        if "boot-role=sysmaint" in kernel_cmdline:
            GlobalData.in_sysmaint_mode = True
    except Exception:
        print(
            "ERROR: Cannot open the kernel command line file!",
            file=sys.stderr,
        )
        sys.exit(1)


def wait_for_required_processes() -> None:
    """
    Waits for all processes in the relevant wait_proc_list to be running.
    Ensures at least one second has passed since all processes in the list
    have started.
    """

    print(f"INFO: Wait for wait_for_required_processes...", file=sys.stderr,)

    wait_proc_list: list[str] = (
        GlobalData.sysmaint_wait_proc_list
        if GlobalData.in_sysmaint_mode
        else GlobalData.normal_wait_proc_list
    )
    sleep_count: int = 0

    while True:
        running_proc_list: list[str] = subprocess.run(
            ["ps", "axo", "comm"],
            check=False,
            capture_output=True,
            encoding="utf-8",
        ).stdout.split("\n")
        time.sleep(1)
        sleep_count += 1
        if sleep_count >= GlobalData.wait_proc_timeout:
            print(f"INFO: Wait for wait_for_required_processes timeout.", file=sys.stderr)
            break
        do_retry_loop: bool = False
        for wait_proc in wait_proc_list:
            if wait_proc not in running_proc_list:
                do_retry_loop = True
                break
        if do_retry_loop:
            continue
        print(f"INFO: Wait for wait_for_required_processes success.", file=sys.stderr)
        break


def parse_config_files() -> None:
    """
    Parses config files for wlr_resize_watcher, modifying the ConfigData class
    to reflect the correct configuration state.
    """

    try:
        config_dict: dict[str, Any] = strict_config_parser.parse_config_files(
            conf_item_list=GlobalData.conf_dir_list,
            conf_schema=GlobalData.conf_schema,
            defaults_dict=GlobalData.conf_defaults,
        )
    except Exception:
        print(
            "ERROR: Cannot parse configuration!",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    assert isinstance(config_dict["enable_dynamic_resolution"], bool)
    assert isinstance(config_dict["warn_on_dynamic_resolution_refuse"], bool)
    assert isinstance(config_dict["standard_default_resolution"], str)
    assert isinstance(config_dict["small_default_resolution"], str)
    GlobalData.enable_dynamic_resolution = config_dict[
        "enable_dynamic_resolution"
    ]
    GlobalData.warn_on_dynamic_resolution_refuse = config_dict[
        "warn_on_dynamic_resolution_refuse"
    ]
    GlobalData.standard_default_resolution = config_dict[
        "standard_default_resolution"
    ]
    GlobalData.small_default_resolution = config_dict[
        "small_default_resolution"
    ]
    GlobalData.normal_wait_proc_list = config_dict["normal_wait_proc_list"]
    GlobalData.sysmaint_wait_proc_list = config_dict[
        "sysmaint_wait_proc_list"
    ]
    GlobalData.wait_proc_timeout = config_dict["wait_proc_timeout"]

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

    parse_config_files()

    check_virtualizer_type()
    print(f"INFO: virtualizer: '{GlobalData.virtualizer_str}'", file=sys.stderr)

    check_sysmaint_mode()
    print(f"INFO: in_sysmaint_mode: '{GlobalData.in_sysmaint_mode}'", file=sys.stderr)

    wait_for_required_processes()
    if (
        GlobalData.resize_helper_present
        and GlobalData.enable_dynamic_resolution
    ):
        print(f"INFO: resize_helper_present and GlobalData.enable_dynamic_resolution: yes", file=sys.stderr)
        sync_hw_resolution_with_compositor(None)
    else:
        print(f"INFO: resize_helper_present and GlobalData.enable_dynamic_resolution: no", file=sys.stderr)
        ## If we can't find an active virtualizer helper, set all displays to
        ## a comfortable default display resolution.
        set_all_displays_resolution_to_default()

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
