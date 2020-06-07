#!/bin/bash

find ./rest/restapi/migrations/ ! -name __init__.py ! -name p -maxdepth 1 -type f -delete
docker-compose down
docker volume rm $(docker volume ls -qf dangling=true)
docker-compose up --build