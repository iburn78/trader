#!/bin/bash

financials="$HOME/projects/financials"
tnp="$HOME/projects/tnp"

mkdir -p "${financials}/data_collect/log"
LOG_FILE="${financials}/data_collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

# Run Python scripts
source "${financials}/venv/bin/activate"

cd "${financials}/data_collect"
python -m gen_market_dbs
# python -m gen_financial_records
# Prevent the same code from running twice across cron jobs
/usr/bin/flock -n /tmp/gen_financial_records.lock python -m gen_financial_records

rsync -ruv "${financials}/data_collect/plots/" "${tnp}/public/data/"