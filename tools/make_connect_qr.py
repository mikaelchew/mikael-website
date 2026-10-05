#!/usr/bin/env python3
"""QR code for the connect page (connect.html), for name cards, slides and Mikael's phone.

Writes images/connect-qr.svg (used on the page; sharp at any print size) and
images/connect-qr.png (1200px, for messaging apps and lock-screen images).
High error correction, so a small logo or a scuffed print still scans.

Usage: /usr/bin/python3 tools/make_connect_qr.py      (needs segno)
"""
import os

import segno

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://www.mikaelchew.com/connect"
INK = "#1a1a1a"

qr = segno.make(URL, error="h")
qr.save(os.path.join(ROOT, "images", "connect-qr.svg"), dark=INK, light="#ffffff", border=4, scale=10, xmldecl=False)
qr.save(os.path.join(ROOT, "images", "connect-qr.png"), dark=INK, light="#ffffff", border=4, scale=1200 // (qr.symbol_size()[0]))
print("connect QR:", URL, "version", qr.version, qr.error)
