#!/bin/bash

source ~/.bashrc

PWD=`pwd`
USERNAME=$1
PASSWORD=$2
DATABASE=$3

if [ -n "$USERNAME" -a -n "$PASSWORD" -a -n "$DATABASE" ]
then
    cp config/constants_example.py config/constants.py
    cp configg_example.py configg.py

    mkdir $PWD/dump
    mkdir $PWD/dump/extract
    mkdir $PWD/dump/source
    mkdir $PWD/dump/clean
    mkdir $PWD/dump/load

    sed -i.bak "s,/your_path_here,$PWD,g" config/constants.py
    sed -i.bak s/username_here/$USERNAME/g configg.py
    sed -i.bak s/password_here/$PASSWORD/g configg.py
    sed -i.bak s/database_here/$DATABASE/g configg.py

    mysql --user=$USERNAME --password=$PASSWORD -e "CREATE DATABASE IF NOT EXISTS $DATABASE"
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/core_schema.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/core_data.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/game_data.sql
    mysql --user=$USERNAME --password=$PASSWORD $DATABASE < schema/team_data.sql
else
    echo "-- Please enter 1) username, 2) password, and 3) database name, in that order (sh build.sh username password database_name)"
fi
