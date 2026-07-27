#!/usr/bin/env bash
set -e

echo "=== retak-mesh: Heltec v3 RNode Firmware Flasher ==="
echo ""

if ! command -v rnodeconf &>/dev/null; then
    echo "Installing Reticulum (includes rnodeconf)..."
    pip install rns
fi

echo ""
echo "Plug in your Heltec v3 via USB while holding the BOOT button."
echo "Then press ENTER to start flashing..."
read -r

echo ""
echo "Starting rnodeconf --autoinstall..."
echo "Select these options when prompted:"
echo "  - Board: Heltec LoRa32 v3.0"
echo "  - Frequency: your local ISM band (e.g. 868 or 915)"
echo ""
rnodeconf --autoinstall

echo ""
echo "Done! The Heltec v3 is now an RNode."
echo "Plug it into your phone via USB-OTG and run retak_bridge.py"
