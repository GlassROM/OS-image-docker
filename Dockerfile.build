FROM scratch
USER root
COPY ./archinstall /

RUN systemd-machine-id-setup

# This is intentional. If the chroot is not the most recent, do not bother updating it. Just fail and require a new chroot build
RUN pacman -Syyuu
CMD ["/bin/bash"]
