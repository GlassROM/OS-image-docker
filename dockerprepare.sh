# TODO: strip lsign key, but this is fine as we are currently building locally
TAG=$(openssl rand -base64 128 | tr -dc 'a-z')
echo "tagging as $TAG"
echo $TAG $(date) | tee -a ./archinstall/container-id
rm ./archlinux/etc/machine-id -rvf

find ./archinstall -perm /4000 -type f -exec chmod u-s {} \;
find ./archinstall -perm /2000 -type f -exec chmod g-s {} \;

docker build . --no-cache -t $TAG;

echo FROM $TAG > TAGINFO
