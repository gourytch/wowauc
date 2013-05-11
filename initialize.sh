#! /bin/bash

set -e
set -x

cd $(dirname $0)

./initialize_fs.sh
./initialize_db.sh
