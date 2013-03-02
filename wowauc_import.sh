#! /bin/bash
cd $(dirname $0)
. wowauc.conf

(
date +"started at %Y-%d-%m %H:%M:%S"
python wowauc_import.py
date +"finished at %Y-%d-%m %H:%M:%S"
echo ""
) >>$dir_log/import.log 2>&1

