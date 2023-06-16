# usability enhancements inside virtual machines #

Enables auto login for user `user` in `lightdm`.
`/etc/lightdm/lightdm.conf.d/30_autologin.conf`
https://www.whonix.org/wiki/Desktop#Disable_Autologin

Sets environment variable `QMLSCENE_DEVICE=softwarecontext` as workaround for
"Automatic fallback to softwarecontext renderer".

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
`dist_build_virtualbox=true` or if running inside VirtualBox.
(`systemd-detect-virt` returning `oracle`)
`/usr/bin/vbox-guest-installer`

## How to install `vm-config-dist` using apt-get ##

1\. Download the APT Signing Key.

```
wget https://www.kicksecure.com/keys/derivative.asc
```

Users can [check the Signing Key](https://www.kicksecure.com/wiki/Signing_Key) for better security.

2\. Add the APT Signing Key.

```
sudo cp ~/derivative.asc /usr/share/keyrings/derivative.asc
```

3\. Add the derivative repository.

```
echo "deb [signed-by=/usr/share/keyrings/derivative.asc] https://deb.kicksecure.com bookworm main contrib non-free" | sudo tee /etc/apt/sources.list.d/derivative.list
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

See instructions.

NOTE: Replace `generic-package` with the actual name of this package `vm-config-dist`.

* **A)** [easy](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package/easy), _OR_
* **B)** [including verifying software signatures](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package)

## Contact ##

* [Free Forum Support](https://forums.kicksecure.com)
* [Premium Support](https://www.kicksecure.com/wiki/Premium_Support)

## Donate ##

`vm-config-dist` requires [donations](https://www.kicksecure.com/wiki/Donate) to stay alive!
