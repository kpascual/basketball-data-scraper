#!/bin/bash

source ~/.bashrc

mkdir $PWD/dump
mkdir $PWD/dump/extract
mkdir $PWD/dump/source
mkdir $PWD/dump/clean
mkdir $PWD/dump/load

sed -i.bak "s,/your_path_here,$PWD,g" config/constants.py

sqlite3 metadata/leagues.db < metadata/leagues.dump.sql
