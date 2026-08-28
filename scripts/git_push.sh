#!/bin/bash

financials="$HOME/projects/financials"
data="$HOME/projects/data"

cd "$financials"
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push

cd "$data"
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push