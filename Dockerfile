FROM python:3.9-slim-buster
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /requirements.txt
RUN    pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt  && \
    python3 -m pip install line-protocol-parser 
COPY doraEnrichment.py /app/
WORKDIR /app
CMD ["doraEnrichment.py"]
ENTRYPOINT ["python3"]
