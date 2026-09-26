#!/usr/bin/env bash
# Start the bot in a pty-like console and feed it a real Ctrl+C (0x03).
cd /c/Users/Vasia/MKOAgent-combat-v1 || exit 1
exec .venv/Scripts/python.exe -u main.py
