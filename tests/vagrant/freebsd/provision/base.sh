#!/bin/sh
# provision/base.sh – runs on both freebsd-a and freebsd-b
set -eu

echo ">>> Bootstrapping pkg ..."
ASSUME_ALWAYS_YES=yes pkg bootstrap -q 2>/dev/null || true
pkg update -q

echo ">>> Installing Python 3, sudo, just, bash, and pv ..."
pkg install -y python3 sudo just bash pv

echo ">>> Verifying ZFS kernel module ..."
# OpenZFS is part of the FreeBSD base; load the module if not already present.
kldload zfs 2>/dev/null || kldstat | grep -q zfs
zfs version

echo ">>> Configuring /etc/hosts for peer resolution ..."
grep -q "test nodes" /etc/hosts || cat >> /etc/hosts <<EOF

# test nodes
${LINUX_A_IP}    linux-a
${LINUX_B_IP}    linux-b
${FREEBSD_A_IP}  freebsd-a
${FREEBSD_B_IP}  freebsd-b
EOF

echo ">>> Creating Python virtual environment ..."
python3 -m venv /home/vagrant/venv
/home/vagrant/venv/bin/pip install --quiet -U pip
/home/vagrant/venv/bin/pip install --quiet -r /project/tests/requirements.txt
chown -R vagrant:vagrant /home/vagrant/venv
printf '\n# Activate ZFS test virtual environment\n. /home/vagrant/venv/bin/activate\n' \
  >> /home/vagrant/.profile

echo ">>> Disabling root SSH login ..."
sed -i '' -E '/^#?PermitRootLogin/d' /etc/ssh/sshd_config
echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
service sshd reload

echo ">>> Configuring passwordless sudo for vagrant user ..."
mkdir -p /usr/local/etc/sudoers.d
echo 'vagrant ALL=(ALL) NOPASSWD: ALL' > /usr/local/etc/sudoers.d/vagrant
chmod 0440 /usr/local/etc/sudoers.d/vagrant

echo ">>> Creating flashheart user ..."
if ! id flashheart >/dev/null 2>&1; then
    pw useradd flashheart -s /usr/sbin/nologin -d /nonexistent -w no
fi

echo ">>> Opening port 18432 if pf or ipfw is active ..."
if service pf onestatus >/dev/null 2>&1; then
    echo "pass in proto { tcp udp } to port 18432 keep state" >> /etc/pf.conf
    pfctl -f /etc/pf.conf
fi
if service ipfw onestatus >/dev/null 2>&1; then
    ipfw add allow tcp from any to any dst-port 18432
    ipfw add allow udp from any to any dst-port 18432
    if [ -f /etc/ipfw.rules ]; then
        echo "ipfw add allow tcp from any to any dst-port 18432" >> /etc/ipfw.rules
        echo "ipfw add allow udp from any to any dst-port 18432" >> /etc/ipfw.rules
    fi
fi

echo ">>> Base provisioning complete."
