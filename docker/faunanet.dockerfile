FROM python:3.11-slim

WORKDIR /home

# add install option 
ARG INSTALL_OPTION

# install with the necessary option
RUN pip install faunanet[${INSTALL_OPTION}]
WORKDIR /home/faunanet

# add folders for incoming data and for output and make sure they are mounted
RUN mkdir /home/faunanet/faunanet_data
RUN mkdir /home/faunanet/faunanet_output
RUN mkdir /home/faunanet/faunanet_config 

# add entrypoint
CMD ["faunanet"]