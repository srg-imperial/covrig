#!/bin/bash

die () {
    echo >&2 "$@"
    exit 1
}

SORT=0

while (( "$#" )); do
  case $1 in
    -s|--sort)
      SORT=1
    ;;
    *)
      break;
    ;;
  esac
  shift
done


INPUT=$1
OUTPUT=$2

echo "0 0 0" >pcov
grep -v '#' $INPUT |awk 'BEGIN { FS="," } ; { if ($7+$8 > 0) print NR,$7,$7+$8; }' >>pcov2
if [[ $SORT -eq 1 ]]; then
  sort -n -k 2 pcov2 >> pcov
else
  cat pcov2 >> pcov
fi

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
"$SCRIPT_DIR/internal/barchartplot.sh" pcov "$OUTPUT" 1 1 "Revision" "ELOC" 'set size 0.8,0.8'

rm -f pcov pcov2
