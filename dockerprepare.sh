TAG=$(openssl rand -base64 128 | tr -dc 'a-z')
echo "tagging as $TAG"
echo $TAG $(date) | tee -a ./archinstall/container-id
rm ./archlinux/etc/pacman.d/gnupg -rvf
rm ./archinstall/etc/machine-id -rvf
rm ./archinstall/root/.bash_history -vf

find ./archinstall -perm /4000 -type f -exec chmod u-s {} \;
find ./archinstall -perm /2000 -type f -exec chmod g-s {} \;

docker build . --no-cache -t $TAG;

echo FROM $TAG > TAGINFO
