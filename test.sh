#!/bin/sh

set -e # to fail on first error

echo
echo ----------------- JavaScript ------------------
node test $1 $2

echo
echo ----------------- Python ------------------
echo
python test.py $1 $2

echo
echo ----------------- PHP ------------------
Skipped.
# php -f test.php $1 $2
