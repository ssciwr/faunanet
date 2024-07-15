FROM python:3.11-slim

WORKDIR /root

ENV RUN_CONFIG=""

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg git && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION="tensorflow"

# install with the necessary option
RUN pip install --upgrade pip setuptools wheel && pip install git+https://github.com/ssciwr/iSparrow.git@allow-custom-model-directory#egg=faunanet[${INSTALL_OPTION}] 
RUN pip install --upgrade pip setuptools wheel && pip install faunanet[${INSTALL_OPTION}] 

# copy over start script
RUN python3 -c "import faunanet.faunanet_setup as sps; sps.set_up(None)" && mkdir /root/faunanet/config && mkdir /root/faunanet/data && mkdir /root/faunanet/custom_models

RUN pkgpath=$(python3 -c "import faunanet; from importlib.resources import files; print(files("faunanet"))") && cp $pkgpath/startup_docker.py /root/startup_docker.py

# RUN apt-get remove -y git pkg-config libhdf5-dev build-essential cmake

# add entrypoint
ENTRYPOINT ["python3", "./startup_docker.py"]