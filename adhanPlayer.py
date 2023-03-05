import datetime
import time
import requests
import vlc
import os
import random
import logging
import utils.adhanLogger as adhanLogger
from prometheus_client import start_http_server, Summary, Counter, Gauge

# setting up logger with default from LabLogger
playerLogger = adhanLogger.logging.getLogger(__file__)


## Grafana metric defintions ###
GetLatestPrayerTimes_REQUEST_TIME = Summary('adhan_player_GetLatestPrayerTimes_processing_seconds', 'Time spent processing request for GetLatestPrayerTimes')
loop_counter = Counter('adhan_player_loop_counter', 'Description of counter')
fajr_prayer_guage = Gauge('epoch_to_fajr', 'epoch time for  fajr')
duhr_prayer_guage = Gauge('epoch_to_duhr', 'epoch time for  duhr')
asr_prayer_guage = Gauge('epoch_to_asr', 'epoch time for  asr')
maghrib_prayer_guage = Gauge('epoch_to_maghrib', 'epoch time for  maghrib')
isha_prayer_guage = Gauge('epoch_to_isha', 'epoch time for  isha')

def StripUnwantedFilesFromArray(filesArray):
    # removes any file starting with '.'
    newArray = []
    for f in filesArray:
        if f[0] != ".":
            newArray.append(f)
    return newArray             


def GetRandomIndexForMusicFile(filesArray):
        filesArray = StripUnwantedFilesFromArray(filesArray)
        randomFileIndexFromFilesArray = random.randint(0, len(filesArray) - 1)
        # valid music file
        return filesArray[randomFileIndexFromFilesArray]     


def GetAdhanFile(prayer):
      fileName = ""
      if prayer.lower() == "fajr":
         for root, dirs, files in os.walk('media/fajr', topdown=True):
                fileName = GetRandomIndexForMusicFile(files)
                playerLogger.info("GetAdhanFile:Getting fajr adhan: {}".format(fileName))
                return root + "/" + fileName
      else:
            # pick a random mp3 from the folder
            for root, dirs, files in os.walk('media', topdown=True):
                  fileName = GetRandomIndexForMusicFile(files)
                  playerLogger.info("GetAdhanFile:Getting adhan file: {}".format(fileName))
                  return root + "/" + fileName              




@GetLatestPrayerTimes_REQUEST_TIME.time()
def GetLatestPrayerTimes():
      playerLogger.debug("GetLatestPrayerTimes: making request http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1")
      ts =None
      prayerTimings=None
      pryayerAdhanPlayed = {}
      try:
            r = requests.get('http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1')
            dataset = r.json()
            playerLogger.debug("GetLatestPrayerTimes: response received : {} ".format(r.json()))
            apiPrayerTimings = dataset["data"]["timings"]
            prayerTimings = {}
            # removing renudant timings
            for prayer in apiPrayerTimings:
                if (isOneOfFiveDailyPrayers(prayer)):
                    prayerTimings[prayer] = apiPrayerTimings[prayer]

            print(prayerTimings)
            pryayerAdhanPlayed = {}
            for p in prayerTimings:
                pryayerAdhanPlayed[p] = False

            ts = datetime.datetime.fromtimestamp(int(dataset["data"]["date"]["timestamp"]))
      except Exception as err:
          playerLogger.error("GetLatestPrayerTimes: Error with getting  request http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1: {}".format(err))    
      return (ts, prayerTimings, pryayerAdhanPlayed)


def isOneOfFiveDailyPrayers(prayerName):
     if prayerName.lower() in ("fajr", "dhuhr","asr", "maghrib","isha"):
          return True
     return False

def setPrometheusTimeToPrayerGuages(prayer,thisPrayerTime):

    if (prayer.lower() == "fajr"):
        fajr_prayer_guage.set(thisPrayerTime.timestamp())
    if (prayer.lower() == "dhuhr"):
        duhr_prayer_guage.set(thisPrayerTime.timestamp())
    if (prayer.lower() == "asr"):
        asr_prayer_guage.set(thisPrayerTime.timestamp())
    if (prayer.lower() == "maghrib"):
        maghrib_prayer_guage.set(thisPrayerTime.timestamp())
    if (prayer.lower() == "isha"):
        isha_prayer_guage.set(thisPrayerTime.timestamp())

def calculateTimeToPrayer(pryayerTimes):

    playerLogger.info("calculateTimeToPrayer: Starting")
    currentTime = datetime.datetime.now()
    
    for prayer in prayerTimes:
        prayerHour = (int)(prayerTimes[prayer].split(':')[0])
        prayerMinute = (int)(prayerTimes[prayer].split(':')[1])
        thisPrayerTime = datetime.datetime.combine(datetime.date.today(), datetime.time(prayerHour,prayerMinute))
        setPrometheusTimeToPrayerGuages(prayer,thisPrayerTime)
        playerLogger.debug("calculateTimeToPrayer: " +  str(prayer) + " is at " + str(thisPrayerTime) )
    return None
####
timestamp = None
pryayerTimes = None
adhanPlayed = {}


if __name__ == '__main__':
    start_http_server(8000)
    while True:
        loop_counter.inc()
        if timestamp:
            playerLogger.debug("main:we already have prayer timeings")
            currentTime  = datetime.datetime.now()
            playerLogger.debug("main:currentTime: {}".format(currentTime))
            if timestamp.date() < currentTime.date():
                playerLogger.debug("main:timestamp has expired. getting latest prayer times ")
                timestamp, prayerTimes, adhanPlayed = GetLatestPrayerTimes()
            else:
                # timestamp is valid now to check prayer timings
                playerLogger.debug("main:checking prayer timing match")
                calculateTimeToPrayer(prayerTimes)
                for prayer in prayerTimes:           
                        prayerHour = (int)(prayerTimes[prayer].split(':')[0])
                        if prayerHour == currentTime.hour and adhanPlayed[prayer] ==False: 
                            # found a prayer with the matching hour:
                            playerLogger.info("main:found matching hour for {}".format(prayer))
                            # now check if its actually prayer time or within a few minutes of it?
                            prayerMinutes = (int)(prayerTimes[prayer].split(':')[1])
                            if prayerMinutes - currentTime.minute <= 0 and prayerMinutes - currentTime.minute >= -2:
                                    # play adhan
                                    playerLogger.info("main: initializing player adhan for {}".format(prayer))
                                    adhanPlayed[prayer] = True
                                    try:                                  
                                            fileName = GetAdhanFile(prayer)
                                            playerLogger.info("main:Playing adhan file {} for prayer {}".format(fileName, prayer))
                                            vlcplayer = vlc.MediaPlayer(fileName)
                                            vlcplayer.play()
                                            while vlcplayer.is_playing == True:
                                                continue
                                            pass
                                    except Exception as err:
                                        playerLogger.error("main: error in playing file {}".format(err))

                        else:
                            # adhan has already prayer for this prayer
                            pass
                playerLogger.info("main: No prayer time match has occured. Sleeping 60 seconds")
                time.sleep(60)  
        else:
            playerLogger.info("main: No prayer timing so far")
            timestamp, prayerTimes, adhanPlayed = GetLatestPrayerTimes()
            playerLogger.info("main: Prayer Timings were refreshed on: {}".format(timestamp))