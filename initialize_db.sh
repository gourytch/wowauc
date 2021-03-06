#! /bin/bash

set -e
set -x

cd $(dirname $0)

source ./wowauc.conf

PGx="psql -h $dbhost -d $dbtmpl -U $dbroot -wAt "
PG="psql -h $dbhost -d $dbname -U $dbuser -wAt"

if ! which psql
then
  PGPATH="/opt/PostgreSQL/9.2/bin/"
  export PATH="$PGPATH:$PATH"
fi

if ( $PGx -c '\dg'| grep -e "^$dbuser|" )
then
  echo "user $dbuser already exists."
else
  echo "create new user $dbuser"
  $PGx -c "CREATE ROLE $dbuser ENCRYPTED PASSWORD '$dbpass' LOGIN"
fi

if psql -h $dbhost -U $dbroot -ls -wSAt | grep -e "^$dbname|"
then
  echo "drop old instance of $dbname press ctrl+c to cancel or enter to drop"
  read dummy
  dropdb -h $dbhost -U $dbroot -w $dbname
fi

echo "create database $dbname ..."
createdb -h $dbhost -U $dbroot -w -O $dbuser -E UNICODE $dbname

echo "initialize database ..."
$PG -ef $dir_etc/db_init.sql
$PG -ef $dir_etc/db_init_items.sql
$PG -ef $dir_etc/db_init_indexes.sql

