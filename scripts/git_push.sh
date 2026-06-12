#!/bin/bash

trader="$HOME/projects/trader"

cd "$trader"
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push