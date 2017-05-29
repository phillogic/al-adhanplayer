import datetime
import time
import requests
import pygame
import os
import random

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
                  return root+"/"+fileName
      else:
            #pick a random mp3 from the folder
            for root, dirs, files in os.walk('media',topdown=True):
                  fileName = GetRandomIndexForMusicFile(files)
                  return root+"/"+fileName              


def GetLatestPrayerTimes():
      r = requests.get('http://api.aladhan.com/timingsByCity?city=Sydney&country=AU&method=1')
      dataset = r.json()
      prayerTimings = dataset["data"]["timings"]
      #removing renudant timings
      prayerTimings.pop('Midnight',None)
      prayerTimings.pop('Sunset',None)
      prayerTimings.pop('Sunrise',None)
      prayerTimings.pop('Imsak',None)
      
      
      print prayerTimings
      pryayerAdhanPlayed =  {}
      for p in prayerTimings:
        pryayerAdhanPlayed[p] = False

      ts = datetime.datetime.fromtimestamp(
      int(dataset["data"]["date"]["timestamp"]))
      return (ts, prayerTimings,pryayerAdhanPlayed)


timestamp = None
pryayerTimes = None
adhanPlayed = {}

if __name__ == '__main__':
    while True:
        if timestamp :
            print "we already have prayer timeings"
            currentTime  = datetime.datetime.now()
            print  "The time right now is : " , currentTime
            if timestamp.date() < currentTime.date():
                print "timestamp has expired. get latest "
                timestamp, prayerTimes, adhanPlayed  =GetLatestPrayerTimes()
            else:
                #timestamp is valid now to check prayer timings
                print "checking prayer timing match"
                for prayer in prayerTimes :
                        
                        prayerHour = (int)(prayerTimes[prayer].split(':')[0])
                        if prayerHour == currentTime.hour and adhanPlayed[prayer] ==False: 
                            #found a prayer with the matching hour:
                            print "found matching hour for "  , prayer
                            #now check if its actually prayer time or within a few minutes of it?
                            prayerMinutes  = (int)(prayerTimes[prayer].split(':')[1])
                            if  prayerMinutes - currentTime.minute <=0 and prayerMinutes - currentTime.minute >= -2:
                                    #play adhan
                                    print "playing adhan for " , prayer
                                    adhanPlayed[prayer] =True
                                    pygame.mixer.init()
                                    fileName = GetAdhanFile(prayer)
                                    print "playing adhan " + fileName
                                    pygame.mixer.music.load(fileName)
                                    pygame.mixer.music.play()
                                    while pygame.mixer.music.get_busy() == True:
                                        continue
                                    pass
                        else:
                            #adhan has already prayer for this prayer
                            pass
                print "No prayer time match has occured. Sleeping 30 seconds"
                time.sleep(30)   
        else:
                print " no prayer timing so far"
                timestamp, prayerTimes, adhanPlayed =GetLatestPrayerTimes()
                print "Prayer Timings were refreshed on: " , timestamp 
            

