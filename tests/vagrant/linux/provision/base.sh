#!/usr/bin/env bash
# provision/base.sh – runs on both linux-a and linux-b
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo ">>> Updating package index ..."
apt-get update -qq

echo ">>> Installing ZFS utilities, Python venv support, just, pv, and xz-utils ..."
apt-get install -y -qq --no-install-recommends \
  zfsutils-linux \
  python3-venv \
  pv \
  xz-utils \
  > /dev/null
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/bin

echo ">>> Verifying ZFS kernel module ..."
modprobe zfs
zfs version

echo ">>> Removing ZFS monthly scrub cron job ..."
rm -f /etc/cron.d/zfsutils-linux

echo ">>> Configuring /etc/hosts for peer resolution ..."
grep -q "test nodes" /etc/hosts || cat >> /etc/hosts <<EOF

# test nodes
${LINUX_A_IP}    linux-a
${LINUX_B_IP}    linux-b
${FREEBSD_A_IP}  freebsd-a
${FREEBSD_B_IP}  freebsd-b
EOF

echo ">>> Disabling automatic apt timers (prevents lock contention) ..."
systemctl disable --now apt-daily.timer         2>/dev/null || true
systemctl disable --now apt-daily-upgrade.timer 2>/dev/null || true

echo ">>> Creating Python virtual environment ..."
python3 -m venv /home/vagrant/venv
/home/vagrant/venv/bin/pip install --quiet -U pip
/home/vagrant/venv/bin/pip install --quiet -r /project/tests/requirements.txt
chown -R vagrant:vagrant /home/vagrant/venv
printf '\n# Activate ZFS test virtual environment\n. /home/vagrant/venv/bin/activate\n' \
  >> /home/vagrant/.profile

echo ">>> Disabling root SSH login ..."
sed -i -E '/^#?PermitRootLogin/d' /etc/ssh/sshd_config
echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
systemctl reload ssh

echo ">>> Configuring passwordless sudo for vagrant user ..."
echo 'vagrant ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/vagrant
chmod 0440 /etc/sudoers.d/vagrant

echo ">>> Creating flashheart user ..."
if ! id flashheart &>/dev/null; then
    useradd --shell /usr/sbin/nologin --no-create-home flashheart
fi

echo ">>> Opening port 18432 if ufw is active ..."
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
    ufw allow 18432/tcp
    ufw allow 18432/udp
fi

echo ">>> Base provisioning complete."
