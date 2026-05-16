#!/bin/bash

trader="/home/andy/projects/trader"
tnp="/home/andy/projects/tnp"
LOG_FILE="${trader}/data_collection/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

cd "$trader"
git pull --no-edit origin main

# Run Python scripts
source venv/bin/activate
cd "${trader}/data_collection"
python 00_CompanyHealth.py
python 01_GenMarketDB.py
python 02_VisualizeHealth.py

rsync -ruv "${trader}/data_collection/plots/" "${tnp}/public/data/"

git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push origin main
