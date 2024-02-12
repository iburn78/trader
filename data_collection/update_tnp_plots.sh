#!/bin/bash

local_directory = "/home/andy/projects/trader/data_collection/plots/test/"
tnp_directory = "/home/ubuntu/projects/trader/data_collection/plots/"
private_key = "/home/andy/.tnpartners_keypair.pem"

rsync -ru -i private_key $local_directory ubuntu@tnpartners.net:$tnp_directory

