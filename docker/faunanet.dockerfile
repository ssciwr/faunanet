FROM python:3.11-slim

WORKDIR /home
RUN apt update && apt install -y git && apt clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# pull repo # will later be replaced with git install
RUN git clone https://github.com/ssciwr/iSparrow.git
WORKDIR /home/iSparrow 

# add install option 
ARG INSTALL_OPTION

# install tensorflow lite
RUN pip install .[${INSTALL_OPTION}]
WORKDIR /home

# remove repo again to keep image small 
RUN rm -rf iSparrow 
RUN apt remove -y git && apt autoremove -y && apt clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# add folders for incoming data and for output and make sure they are mounted
RUN mkdir /home/faunanet_data
RUN mkdir /home/faunanet_output
RUN mkdir /home/faunanet_config 

# add entrypoint
CMD ["faunanet"]