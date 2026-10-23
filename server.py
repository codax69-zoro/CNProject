#!/usr/bin/env python3
"""
server.py
=================================================================================
Localhost HTTP Server & Web API for Network Packet Visualizer
Topic:   IP-MAC Address Management & ARP/DHCP Network Simulation
Team:    Ananya, Krishna, Siddhant (Group 12) | MPSTME Computer Networks
Faculty: Prof. Asha Rawat
=================================================================================
Run with: python server.py
Serves the rich interactive packet transfer visualizer at:
  http://localhost:8000
=================================================================================
"""

import http.server
import json
import os
import socket
import sys
import threading
import webbrowser

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from network_manager import IPMACDatabase

PORT = 8000
DIRECTORY = os.path.join(os.path.dirname(__file__), "visualizer")


class NetworkSimulatorHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/mappings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                db = IPMACDatabase()
                data = db.get_all()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        elif self.path == "/" or self.path == "":
            self.path = "/index.html"

        return super().do_GET()

    def log_message(self, format, *args):
        # Clean terminal output
        sys.stdout.write(f"[HTTP] {args[0]} {args[1]} -> {args[2]}\n")


def find_available_port(start_port=8000):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
            port += 1
    return start_port


def start_server():
    port = find_available_port(PORT)
    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, NetworkSimulatorHTTPHandler)

    url = f"http://localhost:{port}"
    print("=" * 72)
    print("  🌐 IP-MAC MANAGEMENT & PACKET TRANSFER VISUALIZER")
    print("  Topic: IP-MAC Address Management & ARP/DHCP Network Simulation")
    print(f"  Team:  Ananya, Krishna, Siddhant (Group 12) | MPSTME")
    print("=" * 72)
    print(f"\n  [+] Server running on local host: \033[92m{url}\033[0m")
    print(f"  [+] Opening browser automatically...")
    print(f"  [+] Press Ctrl+C in this terminal to stop the server.\n")

    # Open browser automatically after 0.8 seconds
    def open_browser():
        webbrowser.open(url)

    threading.Timer(0.8, open_browser).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Shutting down server...")
        httpd.server_close()
        print("[+] Server stopped.")


if __name__ == "__main__":
    start_server()
