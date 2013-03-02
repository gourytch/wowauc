#! /bin/bash

cd $(dirname $0)

. wowauc.conf

(
date +"started at %Y-%d-%m %H:%M:%S"
python wowauc_fetch.py
date +"finished at %Y-%d-%m %H:%M:%S"
echo ""
) >>$dir_log/fetch.log 2>&1

