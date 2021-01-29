# usability enhancements inside virtual machines #

Enables auto login for user `user` in `lightdm`.
`/etc/lightdm/lightdm.conf.d/30_autologin.conf`
https://www.whonix.org/wiki/Desktop#Disable_Autologin

Sets environment variable `QMLSCENE_DEVICE=softwarecontext` as workaround for
Monero bug "Automatic fallback to softwarecontext renderer". [1]

It is not useful to open a screensaver or to power down the desktop for
operating systems that are run inside VMs. There is no real display that could
be saved and no real power that could be saved. From usability perspective it
also is counter intuitive when looking at the VM window and only seeing a
black screen. Therefore it makes sense to disable power savings in VMs.
`/etc/X11/Xsession.d/20kde_screen_locker_disable_in_vms`
`/etc/X11/Xsession.d/20software_rendering_in_vms`
`/etc/X11/Xsession.d/20power_savings_disable_in_vms`
`/etc/profile.d/20_power_savings_disable_in_vms.sh`
`/usr/share/kde-power-savings-disable-in-vms/kdedrc`
`/usr/share/kde-screen-locker-disable-in-vms/kscreenlockerrc`

Disables screen locker when running in VMs because that is not useful either.

Makes setting up a shared folder for virtual machines a bit easier.

* Creates a folder `/mnt/shared` with `chmod 777`, adds a group
"vboxsf", adds user "user" to group "vboxsf". Facilitates auto-mounting of
shared folders.

* Helps using shared folders with VirtualBox and KVM a bit
easier (as in requiring fewer manual steps from the user).

* `/lib/systemd/system/mnt-shared-vbox.service`
* `/lib/systemd/system/mnt-shared-kvm.service`

Set screen resolution 1920x1080 by default for VM in VirtualBox and KVM.
Workaround for low screen resolution 1024x768 at first boot. When using lower
screen resolutions, Xfce will automatically scale down.
`/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/displays.xml`

Installs VirtualBox guest additions if package
`virtualbox-guest-additions-iso` is installed if environment variable
`WHONIX_BUILD_VIRTUALBOX=true` or if running inside VirtualBox.
(`systemd-detect-virt` returning `oracle`)
`/usr/bin/vbox-guest-installer`

[1] https://github.com/monero-project/monero-gui/issues/2878
## How to install `vm-config-dist` using apt-get ##

1\. Download Whonix's Signing Key.

```
wget https://www.whonix.org/patrick.asc
```

Users can [check Whonix Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key) for better security.

2\. Add Whonix's signing key.

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/whonix.gpg add ~/patrick.asc
```

3\. Add Whonix's APT repository.

```
echo "deb https://deb.whonix.org buster main contrib non-free" | sudo tee /etc/apt/sources.list.d/whonix.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `vm-config-dist`.

```
sudo apt-get install vm-config-dist
```

## How to Build deb Package from Source Code ##

Can be build using standard Debian package build tools such as:

```
dpkg-buildpackage -b
```

See instructions. (Replace `generic-package` with the actual name of this package `vm-config-dist`.)

* **A)** [easy](https://www.whonix.org/wiki/Dev/Build_Documentation/generic-package/easy), _OR_
* **B)** [including verifying software signatures](https://www.whonix.org/wiki/Dev/Build_Documentation/generic-package)

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Donate ##

`vm-config-dist` requires [donations](https://www.whonix.org/wiki/Donate) to stay alive!
