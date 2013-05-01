#! /bin/bash

set -e
# set -x

cd $(dirname $0)
source wowauc.conf
test -e $items_ids.bak && rm -f mv $items_ids.bak
test -e $items_ids &&  mv $items_ids{,.bak}

echo "filling $items_ids"
(
test -e $items_ids.bak && cat $items_ids.bak
find $dir_fetched -type f -name '*.json' -exec cat \{\} \; \
| grep '"item":' \
| sed 's/^.*,"item"://; s/,.*$//;'
) \
| sort -n \
| uniq \
>$items_ids

diff $items_ids.bak $items_ids \
| awk '/^> /{print $2;}' \
>$items_ids.new

echo "done. $(cat  $items_ids | wc -w) ids were gathered"
