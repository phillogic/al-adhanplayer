# README #

### What is this repository for? ###

Python code to use the al-adhan (https://github.com/islamic-network/aladhan.com /  https://aladhan.com/)  apis to play a larger variety of aadhans.

Atm. the code is checking only for sydney AEST, but it could be extended to dynamically use the users local geo.

This code is being used on raspberry pi to make it work like an adhan player.

# Pre-Reqs
A Raspberry pi node cluster with networking
ensure ssh keys are configured for use across pi cluster
Need to setup k3s on the pi cluster.
use the awesome: https://github.com/alexellis/k3sup

## Reconnecting into an existing K3s/k3sup setup if the workstation is delte
* Get the k3s.yaml file from the master node. This would be in the /etc/rancher/k3s folder
* copyt this file as "config" into $HOME/.kube folder
* Update config file to point to correct master node ip address or hostname
* confirm with kubectl on workstation

# Troubleshoot adhanplayer pod
Log into the adhanplayer pod  as follows :
` kubectl exec --stdin --tty adhanplayer-597b7cdd77-gszhc -n adhanplayer -- /bin/bash`
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

Troubleshoot by running speaker-test to see if sound card is setup properly in the env

```
pi@pi3:~ $ speaker-test

speaker-test 1.1.8

Playback device is default
Stream parameters are 48000Hz, S16_LE, 1 channels
Using 16 octaves of pink noise
Rate set to 48000Hz (requested 48000Hz)
Buffer size range from 192 to 2097152
Period size range from 64 to 699051
Using max buffer size 2097152
Periods = 4
was set period_size = 524288
was set buffer_size = 2097152
 0 - Front Left 
 ```
 
 ```
 root@adhanplayer-8ccb6b4df-mwxzr:/adhanplayer# speaker-test

speaker-test 1.1.3

Playback device is default
Stream parameters are 48000Hz, S16_LE, 1 channels
Using 16 octaves of pink noise
Rate set to 48000Hz (requested 48000Hz)
Buffer size range from 512 to 65536
Period size range from 512 to 65536
Using max buffer size 65536
Periods = 4
was set period_size = 16384
was set buffer_size = 65536
 0 - Front Left
Time per period = 1.393386
 0 - Front Left
Time per period = 2.728813
 0 - Front Left
Time per period = 2.730527
 0 - Front Left
 ```
 
 

