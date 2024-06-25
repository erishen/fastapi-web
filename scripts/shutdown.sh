#!/bin/sh

cd $(dirname $BASH_SOURCE)
cd ..
appid=$(basename $(pwd))
cd current
appname=python-app-$appid

pm2 delete $appname
pm2 dump