FROM ubuntu:18.04
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media
RUN apt-get update && apt-get install -y software-properties-common gcc && \
    add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.6 python3-distutils python3-pip python3-apt
RUN pip install -r requirements.txt

CMD ["python" , "./adhanPlayer.py"]
