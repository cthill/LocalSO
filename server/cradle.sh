#!/bin/bash

until python src/main.py;
do
    printf "Cradle: restarting server..."
done
