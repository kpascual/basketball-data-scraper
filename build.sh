#!/bin/bash

source ~/.bashrc

PWD=`pwd`
USERNAME=$1
PASSWORD=$2
DATABASE=$3

if [ -n "$USERNAME" -a -n "$PASSWORD" -a -n "$DATABASE" ]
then
    cp libscrape/config/constants_example.py config/constants.py

    mkdir $PWD/dump
    mkdir $PWD/dump/extract
    mkdir $PWD/dump/source
    mkdir $PWD/dump/clean
    mkdir $PWD/dump/load

    sed -i.bak "s,/your_path_here,$PWD,g" config/constants.py
    sed -i.bak s/username_for_database/$USERNAME/g configg.py
    sed -i.bak s/password_for_database/$PASSWORD/g configg.py
    sed -i.bak s/production_database_name/$DATABASE/g configg.py

    mysql --user=$USERNAME --password=$PASSWORD -e "CREATE DATABASE IF NOT EXISTS $DATABASE"
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/core_schema.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/core_data.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/game_data.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/team_data.sql
else
    echo "-- Please enter 1) username, 2) password, and 3) database name, in that order (sh build.sh username password database_name)"
fi
