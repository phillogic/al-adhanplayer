FROM ubuntu:18.04
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media
RUN apt update
RUN apt install -y software-properties-common ca-certificates wget curl
RUN apt-install -y build-essential python-dev libsdl2-dev \
    libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libjpeg-dev libpng12-dev virtualenvwrapper
RUN pip install -r requirements.txt 

CMD ["python" , "./adhanPlayer.py"]
