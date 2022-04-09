###############################################################################################
# kms
# docker-compose build
# docker-compose up -d
###############################################################################################

FROM python:3.6-buster AS kms

ENV TORCH_HOME /knowledge-management-system

WORKDIR ${TORCH_HOME}

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Korean tokenizer(mecab.jar) uses 8080 port , used by classifier
EXPOSE 8081

CMD ["bash", "./runserver.sh"]

