FROM python:3.11-slim

# add nonroot user 
RUN addgroup -S faunanet \
    && adduser -S faunanet -G faunanet

USER faunanet

WORKDIR /home
RUN apt update && apt install --no-install-recommends -y git && apt clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# pull repo # will later be replaced with git install
RUN git clone https://github.com/ssciwr/iSparrow.git
WORKDIR /home/user/iSparrow 

# add install option 
ARG INSTALL_OPTION

# install tensorflow lite
RUN pip install .[${INSTALL_OPTION}]
WORKDIR /home/faunanet

# remove repo again to keep image small 
RUN rm -rf iSparrow 
RUN apt remove -y git && apt autoremove -y && apt clean && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# add folders for incoming data and for output and make sure they are mounted
RUN mkdir /home/faunanet/faunanet_data
RUN mkdir /home/faunanet/faunanet_output
RUN mkdir /home/faunanet/faunanet_config 

# add entrypoint
CMD ["faunanet"]