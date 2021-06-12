FROM ubuntu:18.04
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media
RUN apt-get update
RUN apt-get install alsa-base alsa-utils
RUN apt-get install -software-properties-common 
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get install -y python3.6 python3-distutils python3-pip python3-apt
RUN apt-get install vlc
RUN echo "defaults.pcm.card 1" > /etc/asound.conf
RUN echo "defaults.ctl.card 1" > /etc/asound.conf
RUN pip3 install -r requirements.txt
CMD ["python3" , "./adhanPlayer.py"]
