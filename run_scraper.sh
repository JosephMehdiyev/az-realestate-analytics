#!/bin/bash
# This script runs your scraper in your user environment

# Load your full environment (PATH, Python virtualenv if any, etc.)
export PATH=$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /home/main/A/bina-az

/usr/bin/python3 scraper.py >> scraper.log 2>&1

