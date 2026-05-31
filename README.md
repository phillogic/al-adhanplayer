# README #

### What is this repository for? ###

Python code to use the al-adhan (https://github.com/islamic-network/aladhan.com /  https://aladhan.com/)  apis to play a larger variety of aadhans.

Atm. the code is checking only for sydney AEST, but it could be extended to dynamically use the users local geo.

This code is being used on raspberry pi to make it work like an adhan player.

## Version 2.0+ (FastAPI, k3s Ingress/Services)

This version migrates the API to FastAPI and adds a k3s Ingress/Service layout.

Highlights:
- Server: FastAPI + Uvicorn (Swagger at `/docs`).
- Path prefix: honors `ROOT_PATH=/adhanplayer` for Traefik subpath.
- Internal access: ClusterIP `Service/adhanplayer` on port 8000 for in-cluster clients (e.g., n8n).
- External access: Traefik `Ingress` at `http://tinker/adhanplayer/...` with prefix stripping.

FastAPI endpoints:
- Health: `GET /health`, Ready: `GET /health/ready`, Metrics: `GET /metrics`.
- Player: `GET /api/v1/player/status`, `POST /api/v1/player/preview?prayer=...`, `POST /api/v1/player/volume?level=...`, `POST /api/v1/player/mute`, `POST /api/v1/player/unmute`.
- Prayer: `GET /api/v1/prayer/times`, `POST /api/v1/prayer/refresh`.


Access patterns:
- In-cluster (recommended for n8n): `http://adhanplayer.adhanplayer.svc.cluster.local:8000/...` (no prefix)
- LAN via Traefik: `http://tinker/adhanplayer/...` (with prefix)

Docker image (slim):
- `Dockerfile.slim` uses `python:3.11-slim` with VLC runtime libs and ALSA.
- CI builds arm64 images for Raspberry Pi 4.

CI change summary:
- `.github/workflows/docker_build.yml` uses `file: Dockerfile.slim` and builds `platforms: linux/arm64`.

### Quickstart (k3s)

YAML files in `k8s_deployment/`
- `asound-configmap.yaml`: ConfigMap with ALSA defaults (which audio card to use)
- `deployment.yaml`: Deployment with embedded Namespace (container config, mounts for snd, asound.conf, and media)
- `service.yaml`: ClusterIP Service `adhanplayer` on port 8000
- `middlewares.yaml`: Traefik middlewares for `/adhanplayer` path handling
- `ingress.yaml`: Traefik Ingress exposing `http://tinker/adhanplayer`
- `pvc.yaml`: Documentation on media storage via hostPath (no actual PVC created)

Apply in order (manual):

```bash
kubectl apply -f k8s_deployment/namespace.yaml
kubectl apply -f k8s_deployment/asound-configmap.yaml
kubectl apply -f k8s_deployment/service.yaml
kubectl apply -f k8s_deployment/middlewares.yaml
kubectl apply -f k8s_deployment/ingress.yaml
kubectl apply -f k8s_deployment/deployment.yaml
```

**Add media files via SCP:**
```bash
scp -r ~/Downloads/adhan.mp3 asim@pi48gb:/media/adhanplayer/
```

**Test:**
- LAN: `curl http://tinker/adhanplayer/health`
- In-cluster: `curl http://adhanplayer.adhanplayer.svc.cluster.local:8000/health`

### Media management API

Endpoints (all under `/api/v1/media`):
- `GET /list`: list files/dirs under `MEDIA_DIR` (query: `path`, `recursive`, `include_hidden`).
- `GET /stats`: summary counts/sizes (total and fajr subdir).
- `GET /file`: file metadata by `rel_path`.
- `GET /download`: download file by `rel_path`.
- `POST /upload`: upload one or more files (multipart form `files`, optional `dest` relative folder).
- `DELETE /file`: delete a file by `rel_path`.

Examples:
- List root: `curl -s http://tinker/adhanplayer/api/v1/media/list | jq .`
- Upload: `curl -s -F "files=@media/a1.mp3" -F "files=@media/a2.mp3" "http://tinker/adhanplayer/api/v1/media/upload?dest=fajr" | jq .`
- Download: `curl -L -o /tmp/a1.mp3 "http://tinker/adhanplayer/api/v1/media/download?rel_path=a1.mp3"`
- Delete: `curl -X DELETE "http://tinker/adhanplayer/api/v1/media/file?rel_path=a1.mp3"`

Persistence: uploads and deletions modify `MEDIA_DIR` (`/adhanplayer/media`), which is mounted to the PVC, so changes persist across restarts.

### Media Storage (hostPath)

Media files are stored directly on the Pi host at `/media/adhanplayer` via a `hostPath` volume. This allows easy network access via SCP.

**Setup:**

1) Create the media directory on the Pi host (pi48gb):

```bash
ssh pi@pi48gb "mkdir -p /media/adhanplayer && chmod 755 /media/adhanplayer"
```

2) The Deployment already mounts this path at `/adhanplayer/media` inside the pod. Roll it out:

```bash
kubectl apply -f k8s_deployment/deployment.yaml
kubectl rollout status deploy/adhanplayer -n adhanplayer
```

**Add media files via SCP:**

From your workstation, copy audio files directly to the host:

```bash
# Copy a folder recursively
scp -r ~/Downloads/aadhans/ pi@pi48gb:/media/adhanplayer/

```

**Alternative: Use kubectl cp (if SCP is unavailable)**

```bash
POD=$(kubectl -n adhanplayer get pod -l app=adhanplayer -o jsonpath='{.items[0].metadata.name}')
kubectl cp ~/Downloads/adhan.mp3 adhanplayer/"$POD":/adhanplayer/media/
```

**Notes:**
- Media persists across pod restarts and redeployments (it's on the host, not in the container).
- Ensure `/media/adhanplayer` exists on `pi48gb` before deploying (the hostPath volume uses `DirectoryOrCreate`, so k8s will create it if missing).
- If you change USB devices or need different permissions, adjust the host directory and redeploy the pod.



CI note: the current `k8s_deploy.yml` workflow applies only `deployment.yaml`. Apply the other YAMLs manually once, or update the workflow to apply all of them.

# Pre-Reqs
A Raspberry pi node cluster with networking
ensure ssh keys are configured for use across pi cluster
Need to setup k3s on the pi cluster.
use the awesome: https://github.com/alexellis/k3sup
## ALSA Audio and speakers

The USB speaker is configured via a Kubernetes ConfigMap (`k8s_deployment/asound-configmap.yaml`) which is mounted into the pod at `/etc/asound.conf`. This approach allows you to change the ALSA card index **without rebuilding the Docker image**.

**Current configuration:**
- Card index: 1 (the USB speaker on your Pi)

**To change the ALSA card (e.g., if you add or replace the USB speaker):**

1. First, identify the new card index on the Pi host:
   ```bash
   aplay -l
   ```
   Look for the line with your USB device (e.g., `card 2: UACDemoV1.0`).

2. Update `k8s_deployment/asound-configmap.yaml` with the new card index:
   ```yaml
   data:
     asound.conf: |
       defaults.pcm.card 2
       defaults.ctl.card 2
   ```

3. Apply the updated ConfigMap and restart the deployment:
   ```bash
   kubectl apply -f k8s_deployment/asound-configmap.yaml
   kubectl -n adhanplayer rollout restart deployment/adhanplayer
   ```

4. Verify the change inside the pod:
   ```bash
   POD=$(kubectl -n adhanplayer get pod -l app=adhanplayer -o jsonpath='{.items[0].metadata.name}')
   kubectl -n adhanplayer exec -it $POD -- cat /etc/asound.conf
   kubectl -n adhanplayer exec -it $POD -- aplay -l
   ```

Note: Because the ConfigMap is mounted with `subPath`, the pod must be restarted for the file to update.

## Reconnecting into an existing K3s/k3sup setup if the workstation is delte
* Get the k3s.yaml file from the master node. This would be in the /etc/rancher/k3s folder
* copy this file as "config" into $HOME/.kube folder
* Update config file to point to correct master node ip address or hostname
* confirm with kubectl on workstation

# Troubleshoot adhanplayer pod
Log into the adhanplayer pod  as follows :
` kubectl exec --stdin --tty adhanplayer-597b7cdd77-gszhc -n adhanplayer -- /bin/bash`


 # Github actions: k8s_deployment
 Ensure that you have the corrct kubeconfig in the secrest of the repo
 

# Old References
## white noise to keep blue tooth speaker alive

Created a crontab to run the sox whiteoise sync as part of the docker container to keep the bluetooth speaker from shutting off.


## text 2 speech
install speak and then use via :
* `espeak -s120 -ven+m3 --stdout "Uss Sallam A laikum. This is Fujjirr time" | aplay`
* `espeak -s120 -ven+m3 --stdout "Uss Sallam A laikum. This is zo-hur time" | aplay`
* `espeak -s120 -ven+m3 --stdout "Uss Sallam A laikum. This is Us ur time" | aplay`
* `espeak -s120 -ven+m3 --stdout "Uss Sallam A laikum. This is Mag rib time" | aplay`
* `espeak -s120 -ven+m3 --stdout "Uss Sallam A laikum. This is Isha time" | aplay`
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
 
 

