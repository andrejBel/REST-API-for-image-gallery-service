FROM python:3

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /usr/src/app

RUN apt-get update && apt-get -y install sudo
RUN sudo apt-get -y install python-pygraphviz
RUN sudo apt-get -y install pkg-config
RUN sudo apt-get -y install libgraphviz-dev
RUN sudo apt-get -y install postgresql

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

COPY . /usr/src/app

EXPOSE 8000