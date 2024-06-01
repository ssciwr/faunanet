FROM python:3.11-slim

WORKDIR /home

RUN apt-get update && apt-get install ffmpeg -y --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION

# install tensorflow lite
RUN pip install faunanet[${INSTALL_OPTION}]
WORKDIR /home/faunanet

RUN mkdir /home/faunanet/faunanet_config 

# add entrypoint
CMD ["faunanet"]