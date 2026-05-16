#!/bin/bash

trader="$HOME/projects/trader"
cd "$trader"

git pull --no-edit origin main

source venv/bin/activate

python data_collection/01_GenMarketDB.py

git add data_collection/data/price_DB.feather data_collection/data/volume_DB.feather
git commit -m "$(date '+%Y-%m-%d') pv update"
git push origin main

