#!/bin/bash
# set the environment variables in AWS Lambda

aws lambda update-function-configuration \
    --function-name ${PROJECT_NAME} \
    --environment "Variables={PROJECT_NAME=${PROJECT_NAME},INFOGRAM_API_KEY=${INFOGRAM_API_KEY},INFOGRAM_API_SECRET=${INFOGRAM_API_SECRET}}"
