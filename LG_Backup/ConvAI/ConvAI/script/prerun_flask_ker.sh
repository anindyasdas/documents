#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd -P )"
echo $DIR

# Change app name in select_app.ini
sed -i 's/^name =.*$/name = ker/' ${DIR}/../config/select_app.ini

# Remove generated directories
echo "Removing/copying files"
sudo rm -rf ${DIR}/../transformers/ ${DIR}/../static/

# Copy apps db to neo4j db files
sudo cp -ar ${DIR}/../apps/ker/neo4j ${DIR}/../
cp -ar ${DIR}/run_flask_ker.sh ${DIR}/../runserver.sh
cp -ar ${DIR}/docker-compose_ker.yml ${DIR}/../docker-compose.yml


echo "ToDo: Add contents into apps/ker/dataset and apps/ker/knowledge_extraction/server/image_db"
