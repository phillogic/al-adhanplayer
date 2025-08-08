import unittest
import os
import sys
import adhanPlayer
class TestAdhanPlayerMethods(unittest.TestCase):

    def test_GetAdhanFile(self):
        fajr = adhanPlayer.GetAdhanFile("Fajr")
        self.assertIsNotNone(fajr)
        self.assertTrue(os.path.exists(fajr))
        self.assertTrue(fajr.endswith(".mp3"))

        asr = adhanPlayer.GetAdhanFile("Asr")
        self.assertIsNotNone(asr)
        self.assertTrue(os.path.exists(asr))
        self.assertTrue(asr.endswith(".mp3"))

    def test_StripUnwantedFilesFromArray_In_MediaFolder(self):
        for root, dirs, files in os.walk('media', topdown=True):
            fArray = adhanPlayer.StripUnwantedFilesFromArray(files)
            for f in fArray:
                self.assertNotEqual(f[0], '.')


if __name__ == '__main__':
    unittest.main()
