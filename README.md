# Disables screen locker and power savings when run inside a virtual machine #

It is not useful to open a screensaver or to power down the desktop for
operating systems that are run inside VMs. There is no real display that could
be saved and no real power that could be saved. From usability perspective it
also is counter intuitive when looking at the VM window and only seeing a
black screen. Therefore it makes sense to disable power savings in VMs.

Disables screen locker when running in VMs because that is not useful either.

When not run inside VMs, this package does nothing.
## How to install `power-savings-disable-in-vms` using apt-get ##

1\. Add [Whonix's Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key).

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/whonix.gpg adv --keyserver hkp://ipv4.pool.sks-keyservers.net:80 --recv-keys 916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA
```

3\. Add Whonix's APT repository.

```
echo "deb http://deb.whonix.org stretch main" | sudo tee /etc/apt/sources.list.d/whonix.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `power-savings-disable-in-vms`.

```
sudo apt-get install power-savings-disable-in-vms
```

## How to Build deb Package ##

Replace `apparmor-profile-torbrowser` with the actual name of this package with `power-savings-disable-in-vms` and see [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/apparmor-profile-torbrowser).

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Payments ##

`power-savings-disable-in-vms` requires [payments](https://www.whonix.org/wiki/Payments) to stay alive!
