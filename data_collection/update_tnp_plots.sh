#!/bin/bash

local_directory="/home/andy/projects/trader/data_collection/plots/"
tnp_directory="/home/ubuntu/projects/trader/data_collection/plots/"
private_key="/home/andy/.tnpartners_keypair.pem"
logfile="/home/andy/projects/trader/data_collection/update_tnp_plots.log"

rsync -ruv --progress -e "ssh -i $private_key" "$local_directory" "ubuntu@tnpartners.net:$tnp_directory" > "$logfile"

