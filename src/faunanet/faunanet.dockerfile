FROM python:3.11-slim

WORKDIR /root

ENV RUN_CONFIG=""

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION="tensorflow"

# install with the necessary option
RUN pip install faunanet[${INSTALL_OPTION}]

# copy over start script
RUN mkdir /root/faunanet_config && mkdir /root/faunanet_data && python3 -c "import faunanet.faunanet_setup as sps; sps.set_up(None)"

RUN pkgpath=$(python3 -c "import faunanet; from importlib.resources import files; print(files("faunanet"))") && ls $pkgpath && cp $pkgpath/docker/startup_docker.py /root/startup_docker.py

# add entrypoint
ENTRYPOINT ["python3", "./startup_docker.py"]