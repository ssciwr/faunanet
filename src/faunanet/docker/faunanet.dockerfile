FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg -y --no-install-recommends && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION

# install with the necessary option
RUN pip install faunanet[${INSTALL_OPTION}]
WORKDIR /root

RUN mkdir /root/faunanet_config && mkdir /root/faunanet_data && python3 -c "import faunanet.faunanet_setup as sps; sps.set_up(None)"
# add entrypoint
CMD ["faunanet"]