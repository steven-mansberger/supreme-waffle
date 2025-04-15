#!/bin/bash
cd /home/steven/dev/rss_generator
source venv/bin/activate
python rss_generator.py --update-only --delay 2.0 --bind-address 192.168.0.66 --no-flask