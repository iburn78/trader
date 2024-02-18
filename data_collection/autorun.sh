#!/bin/bash

# venv activation is not necessary if executed in crontab -e as in crontab -e, venv python is specified
# source ~/projects/trader/venv/bin/activate

# following scripts need to be run in .../data_collection
cd ~/projects/trader/data_collection

python dc_05_CompanyHealth.py
python dc_06_Visualize_Health.py

# copying plots to tnpartners.net
plot_directory="/home/andy/projects/trader/data_collection/plots/"
info_directory="/home/andy/projects/trader/data_collection/"
tnp_data_directory="/home/ubuntu/tnp/public/data/"
tnp_info_directory="/home/ubuntu/tnp/public/"
private_key="/home/andy/.tnpartners_keypair.pem"

date >  "$info_directory"update_info.txt
rsync -ruv --progress -e "ssh -i $private_key" "$plot_directory" "ubuntu@tnpartners.net:$tnp_data_directory"
scp -i $private_key "$info_directory"update_info.txt ubuntu@tnpartners.net:$tnp_info_directory
