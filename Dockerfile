FROM ubuntu:18.04

ENV TZ=Australia/Sydney
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN mkdir /adhanplayer
WORKDIR /adhanplayer
COPY requirements.txt /adhanplayer
COPY adhanPlayer.py /adhanplayer
ADD utils /adhanplayer/utils
ADD media /adhanplayer/media

# Install necessary packages
RUN apt-get update && \
    apt-get install -y tzdata alsa-base alsa-utils software-properties-common sox && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get install -y python3.6 python3-distutils python3-pip python3-apt vlc espeak && \
    echo "defaults.pcm.card 0" > /etc/asound.conf && \
    echo "defaults.ctl.card 0" >> /etc/asound.conf && \
    pip3 install -r requirements.txt

# Create the white noise script
RUN echo '#!/bin/bash\nplay -n synth 1 whitenoise vol 0.01' > /adhanplayer/play_white_noise.sh && \
    chmod +x /adhanplayer/play_white_noise.sh

# Add the cron job
RUN echo '* * * * * /adhanplayer/play_white_noise.sh' > /etc/cron.d/play_white_noise && \
    chmod 0644 /etc/cron.d/play_white_noise && \
    crontab /etc/cron.d/play_white_noise

# Ensure cron is started when the container starts
CMD ["sh", "-c", "cron && python3 ./adhanPlayer.py"]
