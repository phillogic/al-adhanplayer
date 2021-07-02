# README #

### What is this repository for? ###

Python code to use the al-adhan (https://github.com/islamic-network/aladhan.com /  https://aladhan.com/)  apis to play a larger variety of aadhans.

Atm. the code is checking only for sydney AEST, but it could be extended to dynamically use the users local geo.

This code is being used on raspberry pi to make it work like an adhan player.

# Docker sound problems
for a list of devices
```
aplay -l
```
```

pi@pi3:~ $ aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
  Subdevices: 8/8
  Subdevice #0: subdevice #0
  Subdevice #1: subdevice #1
  Subdevice #2: subdevice #2
  Subdevice #3: subdevice #3
  Subdevice #4: subdevice #4
  Subdevice #5: subdevice #5
  Subdevice #6: subdevice #6
  Subdevice #7: subdevice #7
card 1: vc4hdmi [vc4-hdmi], device 0: MAI PCM vc4-hdmi-hifi-0 [MAI PCM vc4-hdmi-hifi-0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0 
  ```
``` 
root@adhanplayer-8ccb6b4df-xrp7g:/adhanplayer# aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
  Subdevices: 8/8
  Subdevice #0: subdevice #0
  Subdevice #1: subdevice #1
  Subdevice #2: subdevice #2
  Subdevice #3: subdevice #3
  Subdevice #4: subdevice #4
  Subdevice #5: subdevice #5
  Subdevice #6: subdevice #6
  Subdevice #7: subdevice #7
card 1: vc4hdmi [vc4-hdmi], device 0: MAI PCM vc4-hdmi-hifi-0 [MAI PCM vc4-hdmi-hifi-0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```                         
