FROM python:3.6-slim

COPY ./requirements.txt /mnt

WORKDIR /mnt

RUN apt-get update && apt-get upgrade -y

RUN apt-get install gcc git libxml2-dev libxslt1-dev zlib1g-dev g++ libsnappy-dev python-snappy -y

RUN pip install -r requirements.txt

RUN pip install git+git://github.com/CityBaseInc/pdfscrape.git git+git://github.com/CityBaseInc/cityscrape.git
