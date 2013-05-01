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

echo "done. $(cat  $items_ids | wc -w) ids were gathered"

if [ -e $items_ids.bak -a -e$items_ids ]; then
new_ids="$items_ids.new-$(date +'%Y%m%d_%H%M%S')"
  diff $items_ids.bak $items_ids \
  | awk '/^> /{print $2;}' \
  >$new_ids
  echo "$(cat $new_ids $ | wc -w) new ids were added"
fi
