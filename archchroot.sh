#!/usr/bin/env bash
set -euo pipefail
error_handler() {
    echo "An error occurred. Aborting!"
    sleep 60
    reboot
    echo "If you see this message, your system did not reboot successfully. Please reboot manually"
    exit 2
}

# Trap errors and call the error_handler function
trap error_handler ERR
trap "reboot" EXIT
if [ -d "./archinstall" ]; then
    echo "chroot directory already exists. To prevent any damage to your system the system will reboot in 10 seconds. After the reboot, run rm -rf ./archinstall before running this again"
    sleep 10
    reboot
    # Reboot calls can return and not actually reboot, which may still lead to system damage.
    # Assume we know nothing about the call and exit manually to ensure processing stops
    echo "If you see this message, your system did not reboot successfully. Please reboot manually"
    exit 1
fi
echo "After the chroot is created, the system will auto reboot to ensure nothing from the host is mounted!"
echo "Save all your work!"
mkdir -p ./archinstall
# Install all of our dependencies and some debugging packages now to save repeating installation steps
pacstrap -C ./pacman.conf ./archinstall base vi vim nano htop mailcap libxcrypt
cp /etc/pacman.conf ./archinstall/etc/pacman.conf
cp /etc/locale.conf ./archinstall/etc/locale.conf
cp /etc/locale.gen ./archinstall/etc/locale.gen
arch-chroot ./archinstall locale-gen
cp /etc/ld.so.preload ./archinstall/etc/ld.so.preload
# Install hardened malloc and anything else from the system into the image
# Dependency handling for additional libraries is an exercise left for the reader. Do NOT attempt to copy dependencies from the host unless the host has also been updated or you will break the chroot. You also need to handle symlinks well. Good luck
for i in $(cat /etc/ld.so.preload); do
    cp $i ./archinstall/$i
done
echo "umask 0077" >>./archinstall/etc/profile

# Test hardened malloc
arch-chroot ./archinstall ldd /bin/bash

arch-chroot ./archinstall pacman -Syyuu --noconfirm
echo "yes | pacman -Scc" > ./archinstall/cleanup
arch-chroot ./archinstall /bin/bash /cleanup
rm ./archinstall/cleanup
echo "Done. System will restart in 15 seconds"
sleep 15
echo "If you see this message, your system did not reboot successfully. Please reboot manually"
