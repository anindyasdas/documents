#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd -P )"
echo $DIR

# Change app name in select_app.ini
sed -i 's/^name =.*$/name = ker_ko/' ${DIR}/../config/select_app.ini

# Remove generated directories
echo "Removing/copying files"
sudo rm -rf ${DIR}/../transformers/ ${DIR}/../static/

# Copy apps db to neo4j db files
sudo cp -ar ${DIR}/../apps/ker_ko/neo4j ${DIR}/../
cp -ar ${DIR}/run_flask_ker_ko.sh ${DIR}/../runserver.sh
cp -ar ${DIR}/docker-compose_ker_ko.yml ${DIR}/../docker-compose.yml

echo "ToDo: Add contents into apps/ker_ko/dataset and apps/ker_ko/knowledge_extraction/server/image_db"
