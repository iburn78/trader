#!/bin/bash

trader="$HOME/projects/trader"
tnp="$HOME/projects/tnp"

mkdir -p "${trader}/data_collect/log"
LOG_FILE="${trader}/data_collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

# Run Python scripts
source "${trader}/venv/bin/activate"

cd "${trader}/data_collect"
python -m gen_market_dbs
python -m gen_financial_records

rsync -ruv "${trader}/data_collect/plots/" "${tnp}/public/data/"