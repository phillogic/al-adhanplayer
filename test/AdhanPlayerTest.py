import unittest
import os
import sys

from player import adhanPlayer
class TestAdhanPlayerMethods(unittest.TestCase):
    
    def test_GetAdhanFile(self):
       fajr =  adhanPlayer.GetAdhanFile("Fajr")
       #print fajr
       self.assertIsNotNone(fajr)
       asr =  adhanPlayer.GetAdhanFile("Asr")
       #print asr
       self.assertIsNotNone(asr)

    def test_StripUnwantedFilesFromArray_In_MediaFolder(self):
        
        for root, dirs, files in os.walk('media',topdown=True):
                  #print files
                  #print "files after strip :", adhanPlayer.StripUnwantedFilesFromArray(files)
                  fArray = adhanPlayer.StripUnwantedFilesFromArray(files)
                  for f in fArray:
                      self.assertNotEqual(f[0],'.')

if __name__ == '__main__':
    unittest.main()