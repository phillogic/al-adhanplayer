FROM alpine:latest
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media
RUN sudo apt-get install build-essential python-dev libsdl2-dev \
    libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libjpeg-dev libpng12-dev virtualenvwrapper
RUN pip3 install -r requirements.txt 

CMD ["python3" , "./adhanPlayer.py"]
