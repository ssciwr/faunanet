FROM python:3.11-slim

WORKDIR /root

ENV RUN_CONFIG=""

# RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg git pkg-config libhdf5-dev build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

# add install option 
ARG INSTALL_OPTION="tensorflow-arm"

RUN if [ "$INSTALL_OPTION" = "tensorflow" ]; then echo "tensorflow is not supported as INSTALL_OPTION on arm architectures. Use tensorflow-arm instead" >&2; exit 1; fi

# install with the necessary option
RUN pip install --upgrade pip setuptools wheel && pip install faunanet[${INSTALL_OPTION}] 

# copy over start script
RUN python3 -c "import faunanet.faunanet_setup as sps; sps.set_up(None)" && mkdir /root/faunanet/config && mkdir /root/faunanet/data && mkdir /root/faunanet/custom_models

RUN pkgpath=$(python3 -c "import faunanet; from importlib.resources import files; print(files("faunanet"))") && cp $pkgpath/startup_docker.py /root/startup_docker.py

# add entrypoint
ENTRYPOINT ["python3", "./startup_docker.py"]