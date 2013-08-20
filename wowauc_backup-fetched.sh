#! /bin/bash
set -e
name=data-fetched

cd $(dirname $0)
if [ ! -d $name ]
then
  echo "nothing to backup (missing directory $name)"
  exit 1
fi

if [ -d tmp/$name ]
then
  echo "directory tmp/$name exists. backup in progress?"
  exit 1
fi

mkdir -p tmp
mv $name tmp/$name
mkdir -p $name

cd tmp/$name

ts_first=`ls -1 | sort -n | head -n1 | sed -e 's|\.json$||'`
ts_last=`ls -1 | sort -n | tail -n1 | sed -e 's|\.json$||'`

if [ "x$ts_first" = "x" ]; then
  echo "empty ts_first !"
  exit 1
fi

if [ "x$ts_last" = "x" ]; then
  echo "empty ts_last !"
  exit 1
fi


zname=$name-${ts_first}-${ts_last}.tar.xz

echo ""
echo "zip $name to $zname"

tar --xz -cnvf ../../$zname.tmp $(ls -1)
cd ../..
mv $zname.tmp $zname
rm -rf tmp
