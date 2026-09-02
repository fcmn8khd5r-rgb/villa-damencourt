#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reçoit le HTML rendu de chaque page et l'écrit sur le disque.

Le site s'assemble dans le navigateur : son apparence n'existe que dans le
DOM rendu, les styles étant posés en ligne par React. Pour le figer en pages
statiques il faut donc récupérer ce DOM — et le faire transiter autrement
que par la conversation, qui n'est pas un tuyau à 139 Ko.

    python3 src/recepteur.py     # écoute sur 8141, écrit dans src/capture/
"""
import http.server, json, os, socketserver

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(RACINE, "src", "capture")


class Recepteur(http.server.BaseHTTPRequestHandler):
    def _entetes(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_OPTIONS(self):
        self._entetes(204)

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        d = json.loads(self.rfile.read(n).decode("utf-8"))
        nom = "".join(c for c in d.get("nom", "sans-nom") if c.isalnum() or c in "-_")
        chemin = os.path.join(DEST, nom + ".html")
        open(chemin, "w", encoding="utf-8").write(d.get("html", ""))
        print("  reçu : %-14s %6d octets" % (nom, len(d.get("html", ""))), flush=True)
        self._entetes()
        self.wfile.write(json.dumps({"ok": True, "octets": len(d.get("html", ""))}).encode())

    def log_message(self, *a):
        pass


os.makedirs(DEST, exist_ok=True)
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 8141), Recepteur) as s:
    print("récepteur à l'écoute sur 8141", flush=True)
    s.serve_forever()
