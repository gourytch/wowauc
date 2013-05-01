#! /bin/bash

cd $(dirname $0)

. wowauc.conf

mkdir -p $dir_fetched_items
(
date +"started at %Y-%d-%m %H:%M:%S"
python wowitem_fetch.py
date +"finished at %Y-%d-%m %H:%M:%S"
echo ""
) >>$dir_log/item_fetch.log 2>&1

