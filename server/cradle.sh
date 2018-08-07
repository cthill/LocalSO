#!/bin/bash

until python src/main.py;
do
    echo "Cradle: non-zero exit code..."
    while [[ $(netstat --inet -natp | grep ":3104\|:3105" | grep "TIME_WAIT") ]]; do
        echo "Cradle: waiting for socket close..."
        sleep 5
    done
    echo "Cradle: restarting server..."
done
