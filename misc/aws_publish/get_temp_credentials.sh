#!/bin/bash

if [[ -z $1 || $1 == --help ]]; then
   echo No env file specified. >&2
   echo Usage: "$0" \<file to write credentials to\> >&2
   exit 255
fi

envfile=$1

awsjson=$(aws  sts get-session-token)

if [[ -z $awsjson ]]; then 
    echo got no proper response from aws sts >&2
    exit 254
fi

set -e

keyid=$(echo "$awsjson"|jq .Credentials.AccessKeyId|tr -d \")
key=$(echo "$awsjson"|jq .Credentials.SecretAccessKey|tr -d \")
token=$(echo "$awsjson"|jq .Credentials.SessionToken|tr -d \")
expiration=$(echo "$awsjson"|jq .Credentials.Expiration|tr -d \")

{
	echo export AWS_ACCESS_KEY_ID=\""$keyid"\" 
	echo export AWS_SECRET_ACCESS_KEY=\""$key"\"
	echo export AWS_SESSION_TOKEN=\""$token"\"
	echo export AWS_REGION=us-east-1
} > "$envfile"

echo Key/token expires at "$expiration"
echo You can now use
echo source "$envfile"
echo to load the credentials into your current shell.

if [[ -z $AWS_ACCOUNT ]]; then
    echo '   **WARNING**'
    echo The AWS_ACCOUNT env var is empty or unset.
    echo Running e.g. deploy.py will not work without it.
fi
