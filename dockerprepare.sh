#!/usr/bin/env bash
echo "Please enter your GitHub personal access token: "
read -s TOKEN
TAG=$(openssl rand -base64 128 | tr -dc 'a-z')
echo "tagging as $TAG"
echo $TAG $(date) | tee -a ./archinstall/container-id
rm ./archinstall/etc/pacman.d/gnupg -rvf
rm ./archinstall/etc/machine-id -rvf
rm ./archinstall/root/.bash_history -vf

cp ../seccomp-mdwe/seccomp-error ./archinstall -av
cp ../seccomp-mdwe/seccomp-strict ./archinstall -av

reflector --latest 50 --age 24 --protocol https --save ./archinstall/etc/pacman.d/mirrorlist

find ./archinstall -perm /4000 -type f -exec chmod u-s {} \;
find ./archinstall -perm /2000 -type f -exec chmod g-s {} \;

./dockersafebuild -t $TAG;

echo FROM $TAG > TAGINFO
echo $TOKEN | docker login ghcr.io -u randomhydrosol --password-stdin
docker tag $TAG ghcr.io/glassrom/os-image-docker:latest
docker push ghcr.io/glassrom/os-image-docker:latest
cosign sign ghcr.io/glassrom/os-image-docker:latest
reboot
