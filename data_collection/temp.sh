#!/bin/bash


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

# hand over info and log files
date > "$info_directory"update_info.txt
scp -i $private_key "$info_directory"update_info.txt ubuntu@tnpartners.net:$tnp_info_directory
scp -i $private_key "$log_directory"*.log ubuntu@tnpartners.net:$tnp_log_directory

