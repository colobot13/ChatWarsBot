#!/bin/bash
/home/trololo/tg/bin/telegram-cli --json -P 1392 -e "dialog_list" -d &
python3 /home/trololo/tg/scripts/main.py --admin '' --order '' --castle ''
