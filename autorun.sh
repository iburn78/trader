#!/bin/bash

# note: if this autorun.sh itself is modified, 
# on the first cron-run this changes may not be reflected
# as changes are updated through 'git pull' below

trader="$HOME/projects/trader"
tnp="$HOME/projects/tnp"
mkdir -p "${trader}/data_collect/log"
LOG_FILE="${trader}/data_collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

cd "$trader"
git pull --no-edit origin main

# Run Python scripts
source venv/bin/activate
cd "${trader}/data_collect"
python 00_gen_market_dbs.py
python 01_gen_financial_records.py

rsync -ruv "${trader}/data_collect/plots/" "${tnp}/public/data/"

git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push origin main
