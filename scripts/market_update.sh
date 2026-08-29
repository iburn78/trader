#!/bin/bash

financials="$HOME/projects/financials"
data="$HOME/projects/data"

mkdir -p "${financials}/collect/log"
LOG_FILE="${financials}/collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

# Run Python scripts
source "${financials}/venv/bin/activate"

cd "${financials}/collect"
python -m gen_market_dbs

mkdir -p "${data}/market"
rsync -ruv "${financials}/collect/data/" "${data}/market/"