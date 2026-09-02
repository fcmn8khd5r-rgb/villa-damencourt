#!/bin/bash
# Double-cliquez pour ouvrir Villa Damencourt.
# Fermez cette fenêtre Terminal pour tout arrêter.

cd "$(dirname "$0")" || exit 1
PORT=8140
while lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; do PORT=$((PORT + 1)); done

echo "Villa Damencourt"
echo "http://localhost:$PORT/Villa%20Damencourt.dc.html"
echo "Laissez cette fenêtre ouverte pendant la consultation."
echo

python3 -m http.server $PORT >/dev/null 2>&1 &
SERVEUR=$!
trap 'kill $SERVEUR 2>/dev/null' EXIT
sleep 1
open "http://localhost:$PORT/Villa%20Damencourt.dc.html"
wait $SERVEUR
