FROM ubuntu:latest

RUN mkdir -p /root/data_extractor
WORKDIR /root/data_extractor
ADD . ./
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

ENTRYPOINT python3 main.py
