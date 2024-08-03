FROM ubuntu:22.04

ENV TZ=Australia/Sydney
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media

# Install necessary packages
RUN apt-get update

RUN apt-get install -y tzdata
RUN apt-get install -y alsa-base alsa-utils
RUN apt-get install -y software-properties-common 
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get install -y python3-distutils python3-pip python3-apt
RUN apt-get install -y vlc
RUN apt-get install -y espeak
RUN echo "defaults.pcm.card 0" > /etc/asound.conf
RUN echo "defaults.ctl.card 0" >> /etc/asound.conf
RUN apt-get install -y sox
RUN apt-get install -y cron


RUN pip3 install -r requirements.txt


# Create the white noise script
RUN echo '#!/bin/bash\nplay -n synth 1 whitenoise vol 0.01' > /adhanplayer/play_white_noise.sh
RUN chmod +x /adhanplayer/play_white_noise.sh

# Add the cron job
RUN echo '* * * * * /adhanplayer/play_white_noise.sh' > /etc/cron.d/play_white_noise
RUN chmod 0644 /etc/cron.d/play_white_noise
RUN crontab /etc/cron.d/play_white_noise

# Ensure cron is started when the container starts
CMD ["sh", "-c", "cron && python3 ./adhanPlayer.py"]
