FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg -y --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION

# install with the necessary option
RUN pip install faunanet[${INSTALL_OPTION}]
WORKDIR /root/faunanet

RUN mkdir /root/faunanet/faunanet_config 

# add entrypoint
CMD ["faunanet"]