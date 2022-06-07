#!/bin/bash

OUTPUT_DIR="../data/pdfs/ICPR/"
URL="https://rd.springer.com/content/pdf/10.1007%2F978-3-030-68763-2_"
mkdir -p $OUTPUT_DIR

for ID in $(seq 60); do
  FILE=$OUTPUT_DIR/icpr_"$ID".pdf
  if [ ! -f FILE ]
then
    wget -O "$FILE" $URL"$ID"
fi

sleep 5
done
