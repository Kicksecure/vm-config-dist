# Disables screen locker and power savings when run inside a virtual machine #

It is not useful to open a screensaver or to power down the desktop for
operating systems that are run inside VMs. There is no real display that could
be saved and no real power that could be saved. From usability perspective it
also is counter intuitive when looking at the VM window and only seeing a
black screen. Therefore it makes sense to disable power savings in VMs.

Disables screen locker when running in VMs because that is not useful either.

When not run inside VMs, this package does nothing.
## How to install `vm-config-dist` using apt-get ##

1\. Download [Whonix's Signing Key]().

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

See [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/vm-config-dist). (Replace `package-name` with the actual name of this package.)

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Donate ##

`vm-config-dist` requires [donations](https://www.whonix.org/wiki/Donate) to stay alive!
