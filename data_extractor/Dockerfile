FROM python:3.9

RUN mkdir -p /root/data_extractor
WORKDIR /root/data_extractor
ADD . ./
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
ENV PYTHONUNBUFFERED=1

ENTRYPOINT python3 main.py
