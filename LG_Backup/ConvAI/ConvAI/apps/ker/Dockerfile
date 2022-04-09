#python:3.6-buster  -> Debian 10(Buster) is considered latest fix than Ubuntu. Python tags had only debian, debian-slim and alpine.
#tensorflow/tensorflow:1.13.1-py3   -> Tensorflow had python3.5 but required py3.6 so we were limited with pip installations
#ubuntu:18.04   ->  Basic Ubuntu had lot of missing entries. Even if we do all installs it becomes heavy.
FROM python:3.6-buster

WORKDIR /ker

COPY requirements.txt /ker

# Pip upgrade + "--no-cache-dir"  was necessary as the caches were not removed whenever there was a download crash and the hash code mismatched.
RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /ker

#NLTK related installation
RUN python -m nltk.downloader stopwords punkt wordnet
RUN python -m spacy download en

EXPOSE 8007

CMD ["python", "-m", "knowledge_extraction.server.flask_main"]
