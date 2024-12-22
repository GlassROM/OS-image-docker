mkfs.erofs  archlinux.img archinstall
python resize.py
dd if=archlinux.img of=/dev/disk/by-id/scsi-360022480e4c7674a98a428fbf7c5612a-part3 bs=1G status=progress
umount /boot
mkfs.vfat -F32 /dev/disk/by-id/scsi-360022480e4c7674a98a428fbf7c5612a-part2
mount /dev/disk/by-id/scsi-360022480e4c7674a98a428fbf7c5612a-part2 /boot
python avb.py archlinux.img | tee AVBOPTS
cat /etc/kernel/cmdline AVBOPTS > cmdline
mount --bind cmdline /etc/kernel/cmdline
mkdir -p /boot/EFI/BOOT
cp /usr/share/shim-signed/mmx64.efi /boot/EFI/BOOT
cp /usr/share/shim-signed/shimx64.efi /boot/EFI/BOOT/BOOTX64.EFI
cp /usr/lib/modules/$(uname -r)/vmlinuz /boot/vmlinuz-linux-hardened
mkinitcpio -p linux-glassrom-uki
sync
