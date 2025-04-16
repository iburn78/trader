#!/bin/bash

# update from git (moved to crontab run 15 mins before)
# purpose: 1) this way, autorun.sh can be updated before it runs, 2) if git fails for some reason, the script will still run
# cd ~/projects/trader
# git fetch origin
# git merge -X theirs origin/main

# cron-job runs in a new shell, and .bashrc is not sourced 
# sudo cron-job and cron-job will have etc/environment variables
# sh runs in a subshell which inherits the env of parent, but the new setting would only exist while sh is running

# Directories
plot_directory="/home/andy/projects/trader/data_collection/plots/"
info_directory="/home/andy/projects/trader/data_collection/data/"
log_directory="/home/andy/projects/trader/data_collection/log/"
andy_update_directory="/home/andy/projects/trader/data_collection/andy/"
tnp_data_directory="/home/ubuntu/tnp/public/data/"
tnp_info_directory="/home/ubuntu/tnp/public/"
tnp_log_directory="/home/ubuntu/tnp/public/log/"
tnp_andy_update_directory="/home/ubuntu/tnp/public/andy/"
private_key="/home/andy/.tnpartners_keypair.pem"
LOG_FILE="${log_directory}autorun.log"  

# Redirect all output (stdout and stderr) to the log file from here on
# exec > >(tee -a "$LOG_FILE") 2>&1 

# Activate virtual environment 
source ~/projects/trader/venv/bin/activate
cd ~/projects/trader/data_collection

# Run Python scripts
python dc05_CompanyHealth.py
python dc06_GenPriceDB.py
python dc17_QuarterlyAnalysisDB.py
python dc07_VisualizeHealth.py
python dc13_RateChanges.py
python dc16_DailyUpdate.py

# SCP and Rsync commands
scp -i $private_key "${info_directory}df_krx.db" ubuntu@tnpartners.net:$tnp_data_directory
rsync -ruv --progress -e "ssh -i $private_key" "$andy_update_directory" "ubuntu@tnpartners.net:$tnp_andy_update_directory"
rsync -ruv --progress -e "ssh -i $private_key" "$plot_directory" "ubuntu@tnpartners.net:$tnp_data_directory"

# Push git changes
git add -A
git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
git push origin main

# Hand over info and log files
date > "${info_directory}update_info.txt"
scp -i $private_key "${info_directory}update_info.txt" ubuntu@tnpartners.net:$tnp_info_directory

# Ensure all data is flushed to the log file
# exec >&-  # Close file descriptors

# SCP the log files to the server
scp -i $private_key "${log_directory}"*.log ubuntu@tnpartners.net:$tnp_log_directory

# Suspend system after a 60 second delay
sleep 60
sudo rtcwake -m mem -t $(date -d 'today 23:30:00' +%s)
