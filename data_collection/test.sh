#!/bin/bash

echo "certain code runs"

sudo rtcwake -m mem -t $(date -d 'today 13:58:00' +%s)
#sudo rtcwake -m mem -l --date +1m

