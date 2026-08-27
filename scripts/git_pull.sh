#!/bin/bash

financials="$HOME/projects/financials"
data="$HOME/projects/data"

cd "$financials"
git pull --no-edit origin main

cd "$data"
git pull --no-edit origin main