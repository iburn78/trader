#!/bin/bash

trader="$HOME/projects/trader"
tnp="$HOME/projects/tnp"

mkdir -p "${trader}/data_collect/log"
LOG_FILE="${trader}/data_collect/log/autorun.log"

exec >> "$LOG_FILE" 2>&1

# Run Python scripts
source "${trader}/venv/bin/activate"

cd "${trader}/data_collect"
python -m 00_gen_market_dbs