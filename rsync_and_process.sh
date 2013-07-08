#! /bin/bash
set -e
set -x

cd $(dirname $(readlink -f $0))
. wowauc.conf

SRC="/mnt/auto/sshfs/globox/srv/stuff/wowauc/var/zipped"
BUF="$HOME/data"
BAK="$BUF/old"
SBAK="$SRC/old"

mkdir -p $BUF
mkdir -p $BAK
mkdir -p $SBAK

for f in $( find $SRC -mindepth 1 -maxdepth 1 -name 'fetched-*.tar.xz' )
do
  name=$(basename $f)
  if [ -e $BUF/$name -o -e $BAK/$name ]
  then
    continue
  fi

  if [ -e $BUF/$name.tmp ]
  then
    rm -f $BUF/$name.tmp
  fi
  cp $f $BUF/$name.tmp
  mv $BUF/$name.tmp $BUF/$name
  mv $f $SBAK/$name
done


for f in $( find $BUF -mindepth 1 -maxdepth 1 -name 'fetched-*.tar.xz' )
do
  tar xapf $f -C $dir_fetched
  mv $f $BAK/$name
done

./grep_item_ids.sh
./wowitem_fetch_fg.sh
./wowauc_import_fg.sh
./zip-imported.sh

echo "done."

