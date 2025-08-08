import unittest
import os
import sys
import datetime
import adhanPlayer
class TestAdhanPlayerMethods(unittest.TestCase):
    
    def test_GetAdhanFile(self):
       fajr =  adhanPlayer.GetAdhanFile("Fajr")
       #print fajr
       self.assertIsNotNone(fajr)
       asr =  adhanPlayer.GetAdhanFile("Asr")
       #print asr
       self.assertIsNotNone(asr)

    def test_StripUnwantedFilesFromArray_In_MediaFolder(self):
        
        for root, dirs, files in os.walk('media', topdown=True):
            #print files
            #print "files after strip :", adhanPlayer.StripUnwantedFilesFromArray(files)
            fArray = adhanPlayer.StripUnwantedFilesFromArray(files)
            for f in fArray:
                self.assertNotEqual(f[0], '.')

    def test_calculateTimeToPrayer_uses_passed_prayer_times(self):
        """calculateTimeToPrayer should rely on its argument, not global state."""

        # Global prayerTimes intentionally set to an incorrect value
        adhanPlayer.prayerTimes = {'Fajr': '00:00'}

        # Provide correct times through the function argument
        test_times = {'Fajr': '05:00'}
        adhanPlayer.calculateTimeToPrayer(test_times)

        expected = datetime.datetime.combine(
            datetime.date.today(), datetime.time(5, 0)
        ).timestamp()
        self.assertEqual(adhanPlayer.fajr_prayer_guage._value.get(), expected)

if __name__ == '__main__':
    unittest.main()
