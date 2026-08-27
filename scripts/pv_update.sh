#!/bin/bash

financials="$HOME/projects/financials"
data="$HOME/projects/data"

mkdir -p "${financials}/data_collect/log"
LOG_FILE="${financials}/data_collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

# Run Python scripts
source "${financials}/venv/bin/activate"

cd "${financials}/data_collect"
python -m gen_market_dbs

mkdir -p "${data}/market"
rsync -ruv "${financials}/data_collect/data/" "${data}/market/"