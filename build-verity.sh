mkfs.erofs -zzstd,level=9 archlinux.img archinstall
python resize.py
python avb.py archlinux.img | tee AVBOPTS
