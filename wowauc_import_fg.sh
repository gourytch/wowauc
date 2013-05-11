#! /bin/bash
cd $(dirname $0)
. wowauc.conf

T0=$(date +"started at %Y-%d-%m %H:%M:%S")

/usr/bin/time -v python wowauc_import.py

T0=$(date +"finished at %Y-%d-%m %H:%M:%S")
echo "STARTED AT  : $T0"
echo "FINISHED AT : $T1"

