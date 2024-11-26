mkfs.erofs -zzstd,level=6 archlinux.img archinstall
python resize.py
python avb.py archlinux.img | tee AVBOPTS
