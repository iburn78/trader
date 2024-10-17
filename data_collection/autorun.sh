#!/bin/bash

# update from git 
cd ~/projects/trader
# Fetch the latest changes from the remote repository
git fetch origin
# Merge the fetched changes, preferring 'theirs' in case of conflicts
git merge -X theirs origin/main

# venv activation is not necessary if executed in crontab -e as in crontab -e, venv python is specified
# source ~/projects/trader/venv/bin/activate

# following scripts need to be run in .../data_collection
cd ~/projects/trader/data_collection

python dc05_CompanyHealth.py
python dc06_GenPriceDB.py
python dc07_VisualizeHealth.py
python dc13_RateChanges.py
python dc16_DailyUpdate.py

# copying plots to tnpartners.net
plot_directory="/home/andy/projects/trader/data_collection/plots/"
info_directory="/home/andy/projects/trader/data_collection/data/"
log_directory="/home/andy/projects/trader/data_collection/log/"
andy_update_directory="/home/andy/projects/trader/data_collection/andy/"
tnp_data_directory="/home/ubuntu/tnp/public/data/"
tnp_info_directory="/home/ubuntu/tnp/public/"
tnp_log_directory="/home/ubuntu/tnp/public/log/"
tnp_andy_update_directory="/home/ubuntu/tnp/public/andy/"
private_key="/home/andy/.tnpartners_keypair.pem"

scp -i $private_key "$info_directory"df_krx.db ubuntu@tnpartners.net:$tnp_data_directory
rsync -ruv --progress -e "ssh -i $private_key" "$andy_update_directory" "ubuntu@tnpartners.net:$tnp_andy_update_directory"
rsync -ruv --progress -e "ssh -i $private_key" "$plot_directory" "ubuntu@tnpartners.net:$tnp_data_directory"

# push git
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push origin main

# hand over info and log files
date > "$info_directory"update_info.txt
scp -i $private_key "$info_directory"update_info.txt ubuntu@tnpartners.net:$tnp_info_directory
scp -i $private_key "$log_directory"*.log ubuntu@tnpartners.net:$tnp_log_directory

# Suspend system after a 60 second delay
sleep 60
sudo rtcwake -m mem -t $(date -d 'today 23:30:00' +%s)

