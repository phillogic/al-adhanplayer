import datetime
import time
import requests
import pygame


       


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
                           print "potential time for "  , prayer
                           #now check if its actually prayer time or within a few minutes of it?
                           prayerMinutes  = (int)(prayerTimes[prayer].split(':')[1])
                           if  prayerMinutes - currentTime.minute <=0 and prayerMinutes - currentTime.minute >= -2:
                                  #play adhan
                                  adhanPlayed[prayer] =True
                                  pygame.mixer.init()
                                  pygame.mixer.music.load("media/a1.mp3")
                                  pygame.mixer.music.play()
                                  while pygame.mixer.music.get_busy() == True:
                                    continue
                                  pass
                     else:
                           #adhan has already prayer for this prayer
                           print "No prayer times sleeping 30 seconds"
                           time.sleep(30)
                           pass
      else:
            print " no prayer timeings so far"
            timestamp, prayerTimes, adhanPlayed =GetLatestPrayerTimes()
            print "Prayer Timings were refreshed on: " , timestamp 
            

