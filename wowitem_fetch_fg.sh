#! /bin/bash

cd $(dirname $0)

. wowauc.conf

mkdir -p $dir_fetched_items
date +"started at %Y-%d-%m %H:%M:%S"
/usr/bin/time -v python wowitem_fetch.py
date +"finished at %Y-%d-%m %H:%M:%S"

