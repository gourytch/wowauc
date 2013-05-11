#! /bin/bash
set -e

cd $(dirname $0)
mkdir -p tmp
mv data tmp/data
mkdir -p data


name=data-$(date +'%Y%m%d_%H%M%S').tar.xz

echo ""
echo "zip data to $name"

cd tmp/data
tar --xz -cnvf ../../$name.tmp $(ls -1)
cd ../..
mv $name.tmp $name
rm -rf tmp
