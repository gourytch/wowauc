#! /bin/bash

set -e
set -x

cd $(dirname $0)

source ./wowauc.conf

test -d $dir_fetching || mkdir -p $dir_fetching
test -d $dir_fetched || mkdir -p $dir_fetched
test -d $dir_importing || mkdir -p $dir_importing
test -d $dir_imported || mkdir -p $dir_imported
test -d $dir_zipped || mkdir -p $dir_zipped
test -d $dir_log || mkdir -p $dir_log

test -d $dir_fetched_items || mkdir -p $dir_fetched_items
test -d $dir_importing_items || mkdir -p $dir_importing_items
test -d $dir_imported_items || mkdir -p $dir_imported_items
