FROM python:3.12-slim-buster

WORKDIR /home 

ADD . /home 

# pull repo 
RUN git pull git@github.com:ssciwr/iSparrow.git
RUN cd iSparrow 

# install tensorflow version
RUN pip install --no-cache-dir -r  .[tensorflow]

# remove repo again to keep image small 
RUN rm -rf iSparrow 

# add folders for incoming data and for output and make sure they are mounted
RUN mkdir /home/faunanet_data
RUN mkdir /home/faunanet_output
RUN mkdir /home/faunanet_config 

# add entrypoint
CMD ["faunanet"]