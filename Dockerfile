FROM ghcr.io/glassrom/os-image-docker:latest

RUN pacman-key --init && pacman-key --populate archlinux

RUN pacman -Syyuu --noconfirm

RUN rm -rvf /etc/pacman.d/gnupg
