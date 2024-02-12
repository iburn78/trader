#!/bin/bash

# venv activation is not necessary if executed in crontab -e
# source ~/projects/trader/venv/bin/activate

# following scripts need to be run in .../data_collection
cd ~/projects/trader/data_collection

python dc_05_CompanyHealth.py
python dc_06_Visualize_Health.py

# copying plots to tnpartners.net
local_directory="/home/andy/projects/trader/data_collection/plots/"
tnp_directory="/home/ubuntu/tnp/public/"
private_key="/home/andy/.tnpartners_keypair.pem"

date >  "$local_directory"update_info.txt
rsync -ruv --progress -e "ssh -i $private_key" "$local_directory" "ubuntu@tnpartners.net:$tnp_directory"
