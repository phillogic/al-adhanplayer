FROM python:3.7.6-slim-stretch
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media
RUN pip3 install -r requirements.txt 
CMD ["python3" , "./adhanPlayer.py"]
