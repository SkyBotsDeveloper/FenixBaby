#!/bin/bash
# VPS Deployment Script for Fenix Baby
echo "Starting Fenix Baby deployment..."

sudo apt update && sudo apt install -y python3 python3-pip mongodb
pip3 install -r requirements.txt

echo "Make sure BOT_TOKEN, MONGO_URI, OWNER_ID, and ELITE_LLM_API_KEY are set."
echo "Usage: BOT_TOKEN='xxx' MONGO_URI='xxx' OWNER_ID='xxx' ELITE_LLM_API_KEY='xxx' python3 FenixBaby.py"
echo "Setup complete. Use 'python3 FenixBaby.py' to run."
