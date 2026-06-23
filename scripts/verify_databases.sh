#!/usr/bin/env bash
# Quick health check for both databases. No sudo needed.
#   bash scripts/verify_databases.sh
set -uo pipefail

echo "== systemd services =="
echo "neo4j  : $(systemctl is-active neo4j  2>/dev/null || echo unknown)"
echo "qdrant : $(systemctl is-active qdrant 2>/dev/null || echo unknown)"
echo
echo "== Qdrant REST (http://localhost:6333) =="
curl -fsS http://localhost:6333/ && echo || echo "  (no response)"
echo "collections:"
curl -fsS http://localhost:6333/collections && echo || echo "  (no response)"
echo
echo "== Neo4j HTTP (http://localhost:7474) =="
curl -fsS http://localhost:7474/ >/dev/null && echo "  reachable" || echo "  (no response)"
