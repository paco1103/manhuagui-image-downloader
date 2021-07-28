FROM python:3.7.11

RUN mkdir /app
WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV DISPLAY :1
