FROM python:3.11.8-alpine as build

ENV TZ Asia/Seoul

WORKDIR /home/app
COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY .env .env