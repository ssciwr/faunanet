FROM python:3.11-slim

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg git && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV RUN_CONFIG=""

ENV USER_ID=1000

ENV GROUP_ID=1000

# add install option 
ARG INSTALL_OPTION="tensorflow"

RUN addgroup --gid $GROUP_ID faunanet

RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID faunanet

USER faunanet

WORKDIR /home/faunanet

# install with the necessary option
RUN pip install "git+https://github.com/ssciwr/iSparrow@add-docker-files#egg=faunanet[tensorflow]"

# copy over start script
RUN mkdir /home/faunanet/config && mkdir /home/faunanet/data && python3 -c "import faunanet.faunanet_setup as sps; sps.set_up(None)"

RUN pkgpath=$(python3 -c "import faunanet; from importlib.resources import files; print(files("faunanet"))") && cp $pkgpath/startup_docker.py /home/faunanet/startup_docker.py

RUN export PYTHONPATH=$PYTHONPATH:/home/faunanet

# add entrypoint
ENTRYPOINT ["python3", "./startup_docker.py"]