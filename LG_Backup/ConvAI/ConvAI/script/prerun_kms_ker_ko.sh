#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd -P )"
echo $DIR

# Change app name in select_app.ini
sed -i 's/^name =.*$/name = ker_ko/' ${DIR}/../config/select_app.ini

# Change neo4j port for connection
sed -i 's/host.docker.internal:..../host.docker.internal:8043/' ${DIR}/../apps/ker_ko/knowledge_extraction/config/configuration.ini

# Change ker_ko server port for connection
sed -i 's/^port_number = .*$/port_number = 8008/' ${DIR}/../apps/ker_ko/knowledge_extraction/config/configuration.ini

# Change runserver.sh
git checkout ${DIR}/../runserver.sh
sed -i 's/0.0.0.0:.*$/0.0.0.0:8083/' ${DIR}/../runserver.sh

# Remove generated directories
echo "Removing/copying files"
sudo rm -rf ${DIR}/../transformers/ ${DIR}/../static/

# Copy apps db to neo4j db files
sudo cp -ar ${DIR}/../apps/ker_ko/neo4j ${DIR}/../
cp -ar ${DIR}/docker-compose_ker_ko.yml ${DIR}/../docker-compose.yml

echo "ToDo: Add contents into apps/ker/dataset and apps/ker/knowledge_extraction/server/image_db"
