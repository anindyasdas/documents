FROM python:3.6-buster
WORKDIR /docbased
COPY requirements.txt /docbased
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
