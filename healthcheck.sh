#!/bin/sh

HTTP_CODE=$(curl -qs -o /dev/null -w "%{http_code}" -X GET -H "secretkey: $SECRET_KEY" localhost:8000)
RETURN_CODE=$?
if [ "$RETURN_CODE" -eq 0 ]; then
    if [ "$HTTP_CODE" != 200 ]; then
        echo "Return code for localhost:8000 is not 200"
        exit 1
    fi
else
    echo "Can't query localhost:8000 with curl"
    exit 1
fi
