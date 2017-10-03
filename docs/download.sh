#!/bin/bash



for f in */*.pdf
do
    pdfcrop $f $f
done
