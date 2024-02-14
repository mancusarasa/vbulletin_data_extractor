FROM python:3.9

RUN mkdir -p /root/posts_extractor
WORKDIR /root/posts_extractor
ADD . ./
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
ENV PYTHONUNBUFFERED=1

ENTRYPOINT python3 main.py
