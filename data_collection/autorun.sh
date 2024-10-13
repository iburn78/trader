#!/bin/bash

# venv activation is not necessary if executed in crontab -e as in crontab -e, venv python is specified
# source ~/projects/trader/venv/bin/activate

# following scripts need to be run in .../data_collection
cd ~/projects/trader/data_collection

python dc05_CompanyHealth.py
python dc06_GenPriceDB.py
python dc07_VisualizeHealth.py
python dc13_RateChanges.py

# copying plots to tnpartners.net
plot_directory="/home/andy/projects/trader/data_collection/plots/"
info_directory="/home/andy/projects/trader/data_collection/data/"
log_directory="/home/andy/projects/trader/data_collection/log/"
tnp_data_directory="/home/ubuntu/tnp/public/data/"
tnp_info_directory="/home/ubuntu/tnp/public/"
tnp_log_directory="/home/ubuntu/tnp/public/log/"
private_key="/home/andy/.tnpartners_keypair.pem"

scp -i $private_key "$info_directory"df_krx.db ubuntu@tnpartners.net:$tnp_data_directory

rsync -ruv --progress -e "ssh -i $private_key" "$plot_directory" "ubuntu@tnpartners.net:$tnp_data_directory"

date > "$info_directory"update_info.txt
scp -i $private_key "$info_directory"update_info.txt ubuntu@tnpartners.net:$tnp_info_directory

scp -i $private_key "$log_directory"*.log ubuntu@tnpartners.net:$tnp_log_directory

# Check if file transfers were successful
if [ $? -eq 0 ]; then 
    # Navigate to the git directory
    cd ~/projects/trader

    # Add all changes, commit with today's date, and push
    git add -A
    git commit -m "$(date '+%Y-%m-%d') upload done from linux machine"
    git push
    git pull

    # Suspend system after a 60 second delay
    sleep 60
    sudo rtcwake -m mem -t $(date -d 'today 23:30:00' +%s)
else
    echo "Local system suspend error"
fi


