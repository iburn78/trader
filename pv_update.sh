#!/bin/bash

trader="$HOME/projects/trader"
cd "$trader"

git pull --no-edit origin main

source venv/bin/activate

python data_collect/00_gen_market_dbs.py

git add data_collect/data/price_db.feather data_collect/data/volume_db.feather
git commit -m "$(date '+%Y-%m-%d') pv update"
git push origin main

