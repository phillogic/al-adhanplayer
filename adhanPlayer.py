import datetime
import time
import requests
import pygame
import os
import random
import logging
import utils.adhanLogger as adhanLogger


#setting up logger with default from LabLogger
playerLogger= adhanLogger.logging.getLogger(__file__)

def StripUnwantedFilesFromArray(filesArray):
    #removes any file starting with '.'
    newArray = []
    for f in filesArray :
        if f[0] != "." :
            newArray.append(f)
    return newArray              

def GetRandomIndexForMusicFile (filesArray):
      filesArray= StripUnwantedFilesFromArray (filesArray)
      randomFileIndexFromFilesArray =  random.randint(0,len(filesArray) -1 )
       #valid music file
      return  filesArray[randomFileIndexFromFilesArray]     

def GetAdhanFile(prayer):
      fileName =""
      if prayer =="Fajr":
         for root, dirs, files in os.walk('media/fajr',topdown=True):
                  fileName = GetRandomIndexForMusicFile(files)
                  playerLogger.info("GetAdhanFile:Getting fajr adhan: {}".format(fileName))
                  return root+"/"+fileName
      else:
            #pick a random mp3 from the folder
            for root, dirs, files in os.walk('media',topdown=True):
                  fileName = GetRandomIndexForMusicFile(files)
                  playerLogger.info("GetAdhanFile:Getting adhan file: {}".format(fileName))
                  return root+"/"+fileName              


def GetLatestPrayerTimes():
      playerLogger.debug("GetLatestPrayerTimes: making request http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1")
      ts =None
      prayerTimings=None
      pryayerAdhanPlayed = {}
      try:
            r = requests.get('http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1')
            dataset = r.json()
            playerLogger.debug("GetLatestPrayerTimes: response received : {} ".format(r.json()))
            prayerTimings = dataset["data"]["timings"]
            #removing renudant timings
            prayerTimings.pop('Midnight',None)
            prayerTimings.pop('Sunset',None)
            prayerTimings.pop('Sunrise',None)
            prayerTimings.pop('Imsak',None)
            
            
            print (prayerTimings)
            pryayerAdhanPlayed =  {}
            for p in prayerTimings:
                pryayerAdhanPlayed[p] = False

            ts = datetime.datetime.fromtimestamp(
            int(dataset["data"]["date"]["timestamp"]))
      except Exception as err:
          playerLogger.error("GetLatestPrayerTimes: Error with getting  request http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1: {}".format(err))
         
      return (ts, prayerTimings,pryayerAdhanPlayed)


timestamp = None
pryayerTimes = None
adhanPlayed = {}

if __name__ == '__main__':
    while True:
        if timestamp :
            playerLogger.debug( "main:we already have prayer timeings")
            currentTime  = datetime.datetime.now()
            playerLogger.debug( "main:currentTime: {}".format( currentTime))
            if timestamp.date() < currentTime.date():
                playerLogger.debug( "main:timestamp has expired. getting latest prayer times ")
                timestamp, prayerTimes, adhanPlayed  = GetLatestPrayerTimes()
            else:
                #timestamp is valid now to check prayer timings
                playerLogger.debug( "main:checking prayer timing match")
                for prayer in prayerTimes :
                        
                        prayerHour = (int)(prayerTimes[prayer].split(':')[0])
                        if prayerHour == currentTime.hour and adhanPlayed[prayer] ==False: 
                            #found a prayer with the matching hour:
                            playerLogger.info( "main:found matching hour for {}".format( prayer))
                            #now check if its actually prayer time or within a few minutes of it?
                            prayerMinutes  = (int)(prayerTimes[prayer].split(':')[1])
                            if  prayerMinutes - currentTime.minute <=0 and prayerMinutes - currentTime.minute >= -2:
                                    #play adhan
                                    playerLogger.info( "main: initializing player adhan for {}".format( prayer))
                                    adhanPlayed[prayer] =True
                                    try:
                                            pygame.mixer.init()
                                            fileName = GetAdhanFile(prayer)
                                            playerLogger.info( "main:Playing adhan file {} for prayer {}".format(fileName,prayer))
                                            pygame.mixer.music.load(fileName)
                                            pygame.mixer.music.play()
                                            while pygame.mixer.music.get_busy() == True:
                                                continue
                                            pass
                                    except Exception as err:
                                        playerLogger.error("main: error in playing file {}".format(err))

                        else:
                            #adhan has already prayer for this prayer
                            pass
                playerLogger.info( "main: No prayer time match has occured. Sleeping 60 seconds")
                time.sleep(60)   
        else:
                playerLogger.info( "main: No prayer timing so far")
                timestamp, prayerTimes, adhanPlayed =GetLatestPrayerTimes()
                playerLogger.info( "main: Prayer Timings were refreshed on: {}".format( timestamp ))
            

