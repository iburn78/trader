#!/bin/bash

financials="$HOME/projects/financials"

cd "$financials"
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push