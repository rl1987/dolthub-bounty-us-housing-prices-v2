#!/bin/bash

set -x

apt-get update
apt-get install -y python3 python3-pip tmux git vim visidata unzip jq

curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh > /tmp/install.sh && bash /tmp/install.sh
dolt config --global --add user.email rimantas@keyspace.lt
dolt config --global --add user.name "rl1987"

pip3 install --upgrade requests lxml js2xml doltpy scrapy openpyxl pandas xlrd

curl -sSL https://repos.insights.digitalocean.com/install.sh -o /tmp/install.sh
bash /tmp/install.sh

mkdir /root/data

pushd /root/data
dolt clone rl1987/us-housing-prices-v2
dolt remote add upstream dolthub/us-housing-prices-v2
popd /root/data
