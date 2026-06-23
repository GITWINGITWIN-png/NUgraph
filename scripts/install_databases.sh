#!/usr/bin/env bash
#
# Installs Neo4j (Community) + Qdrant natively on Ubuntu, as system services.
#
#   Run from the project root:   bash scripts/install_databases.sh
#
# Uses sudo for the system-level steps; you'll be prompted for your account
# password once. Everything it does is reversible (see scripts/uninstall_databases.sh
# notes in the README).
#
set -euo pipefail

QDRANT_VERSION="v1.18.2"
NEO4J_VERSION="1:2026.05.0"
RUN_USER="$(id -un)"

echo "=========================================================="
echo " NUgraph database install"
echo "   - OpenJDK 21            (Neo4j dependency)"
echo "   - Neo4j Community ${NEO4J_VERSION}   ports 7474 (browser) / 7687 (bolt)"
echo "   - Qdrant ${QDRANT_VERSION}             ports 6333 (rest) / 6334 (grpc)"
echo "=========================================================="
echo

# --- Neo4j password (kept in your shell only; written nowhere by this script) ---
read -rsp "Choose a password for the Neo4j 'neo4j' user: " NEO4J_PASSWORD; echo
if [ -z "${NEO4J_PASSWORD}" ]; then
  echo "ERROR: password cannot be empty." >&2
  exit 1
fi

echo
echo "==> Priming sudo (enter your account password if prompted)..."
sudo -v

# ----------------------------------------------------------------------------
# 1. Java 21 (required by Neo4j 2026.x)
# ----------------------------------------------------------------------------
echo "==> Installing OpenJDK 21..."
sudo apt-get update -y
sudo apt-get install -y openjdk-21-jre-headless

# ----------------------------------------------------------------------------
# 2. Neo4j Community via the official apt repository
# ----------------------------------------------------------------------------
echo "==> Adding the Neo4j apt repository..."
sudo mkdir -p /etc/apt/keyrings
wget -qO - https://debian.neo4j.com/neotechnology.gpg.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/neotechnology.gpg
sudo chmod a+r /etc/apt/keyrings/neotechnology.gpg
echo 'deb [signed-by=/etc/apt/keyrings/neotechnology.gpg] https://debian.neo4j.com stable latest' \
  | sudo tee /etc/apt/sources.list.d/neo4j.list > /dev/null
sudo apt-get update -y

echo "==> Installing Neo4j ${NEO4J_VERSION} (Community)..."
sudo apt-get install -y "neo4j=${NEO4J_VERSION}"

echo "==> Setting the Neo4j initial password..."
sudo systemctl stop neo4j 2>/dev/null || true
# set-initial-password only works before auth has been initialised on first start.
if ! sudo neo4j-admin dbms set-initial-password "${NEO4J_PASSWORD}"; then
  echo "    NOTE: initial password was already set on a previous run; leaving it as-is."
  echo "    If you don't know it, stop neo4j, run 'sudo rm /var/lib/neo4j/data/dbms/auth*',"
  echo "    then re-run this script."
fi

echo "==> Enabling + starting Neo4j..."
sudo systemctl enable neo4j
sudo systemctl start neo4j

# ----------------------------------------------------------------------------
# 3. Qdrant native binary + systemd service (no apt package exists)
# ----------------------------------------------------------------------------
echo "==> Downloading Qdrant ${QDRANT_VERSION}..."
TMP="$(mktemp -d)"
wget -qO "${TMP}/qdrant.tar.gz" \
  "https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-gnu.tar.gz"
tar -xzf "${TMP}/qdrant.tar.gz" -C "${TMP}"

echo "==> Installing the Qdrant binary to /opt/qdrant..."
sudo mkdir -p /opt/qdrant/bin
sudo install -m 0755 "${TMP}/qdrant" /opt/qdrant/bin/qdrant
rm -rf "${TMP}"

echo "==> Creating Qdrant storage directories (owned by ${RUN_USER})..."
sudo mkdir -p /var/lib/qdrant/storage /var/lib/qdrant/snapshots
sudo chown -R "${RUN_USER}:${RUN_USER}" /var/lib/qdrant

echo "==> Writing the Qdrant systemd unit..."
sudo tee /etc/systemd/system/qdrant.service > /dev/null <<UNIT
[Unit]
Description=Qdrant vector database
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=/var/lib/qdrant
Environment=QDRANT__STORAGE__STORAGE_PATH=/var/lib/qdrant/storage
Environment=QDRANT__STORAGE__SNAPSHOTS_PATH=/var/lib/qdrant/snapshots
ExecStart=/opt/qdrant/bin/qdrant
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable qdrant
sudo systemctl start qdrant

# ----------------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------------
echo
echo "==> Waiting a few seconds for services to come up..."
sleep 5
echo
echo "Neo4j  : $(systemctl is-active neo4j)    http://localhost:7474  (user: neo4j)"
echo "Qdrant : $(systemctl is-active qdrant)    http://localhost:6333/dashboard"
echo
echo "NEXT STEPS:"
echo "  1) cp .env.example .env"
echo "  2) put your Neo4j password into .env  (NEO4J_PASSWORD=...)"
echo "  3) tell Claude it's done; it will verify connectivity and continue."
echo
echo "Install complete."
