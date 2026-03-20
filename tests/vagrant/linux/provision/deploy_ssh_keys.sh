#!/usr/bin/env bash
# provision/deploy_ssh_keys.sh – installs shared test keypair for vagrant user (Linux)
set -euo pipefail

SSH_DIR="/home/vagrant/.ssh"

echo ">>> Deploying SSH keypair for vagrant user ..."

# Private key
install -o vagrant -g vagrant -m 0600 /tmp/zfs_test_key  "${SSH_DIR}/id_ed25519"

# Public key
install -o vagrant -g vagrant -m 0644 /tmp/zfs_test_key.pub "${SSH_DIR}/id_ed25519.pub"

# Authorize the key so peers can log in
cat /tmp/zfs_test_key.pub >> "${SSH_DIR}/authorized_keys"
sort -u -o "${SSH_DIR}/authorized_keys" "${SSH_DIR}/authorized_keys"
chown vagrant:vagrant "${SSH_DIR}/authorized_keys"
chmod 0600 "${SSH_DIR}/authorized_keys"

# Disable strict host-key checking for the private test network
# so snapshot-restores don't cause SSH failures.
cat > "${SSH_DIR}/config" <<'EOF'
Host linux-a linux-b freebsd-a freebsd-b 192.168.56.*
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel ERROR
  IdentityFile ~/.ssh/id_ed25519
  User vagrant

Host remotehost
  Hostname localhost
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel ERROR
  IdentityFile ~/.ssh/id_ed25519
  User vagrant

Host *
  ControlMaster auto
  ControlPersist 5m
  ControlPath /tmp/ssh-ctl-%C
  Ciphers chacha20-poly1305@openssh.com,aes128-ctr,aes128-gcm@openssh.com
  MACs umac-128-etm@openssh.com,umac-64-etm@openssh.com
  GSSAPIAuthentication no
  Compression no
EOF
chown vagrant:vagrant "${SSH_DIR}/config"
chmod 0600 "${SSH_DIR}/config"

# Clean up temp files
rm -f /tmp/zfs_test_key /tmp/zfs_test_key.pub

echo ">>> SSH key deployment complete."
