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

Kubernetes manifests (see files under `k8s_deployment/`):
- `deployment.yaml`: Namespace + Deployment (includes `ROOT_PATH` and `MEDIA_DIR`).
- `service.yaml`: ClusterIP `adhanplayer` on port 8000.
- `middlewares.yaml`: Traefik middlewares for `/adhanplayer` path handling.
- `ingress.yaml`: Traefik Ingress exposing `http://tinker/adhanplayer`.
- `pvc.yaml`: PVC `adhanplayer-media` (local-path, node-annotated to `pi48gb`).

Access patterns:
- In-cluster (recommended for n8n): `http://adhanplayer.adhanplayer.svc.cluster.local:8000/...` (no prefix)
- LAN via Traefik: `http://tinker/adhanplayer/...` (with prefix)

Docker image (slim):
- `Dockerfile.slim` uses `python:3.11-slim` with VLC runtime libs and ALSA.
- CI builds arm64 images for Raspberry Pi 4.

CI change summary:
- `.github/workflows/docker_build.yml` uses `file: Dockerfile.slim` and builds `platforms: linux/arm64`.

### Quickstart (k3s)

Apply order
- Create namespace: `kubectl create ns adhanplayer || true`
- Service: `kubectl apply -f k8s_deployment/service.yaml`
- Traefik middlewares: `kubectl apply -f k8s_deployment/middlewares.yaml`
- Ingress: `kubectl apply -f k8s_deployment/ingress.yaml`
- PVC: `kubectl apply -f k8s_deployment/pvc.yaml`
- Deployment: `kubectl apply -f k8s_deployment/deployment.yaml`
- Wait for pod: `kubectl rollout status deploy/adhanplayer -n adhanplayer`

Seed media into PVC
- Get pod: `POD=$(kubectl get po -n adhanplayer -l app=adhanplayer -o jsonpath='{.items[0].metadata.name}')`
- Copy media: `kubectl cp media/. -n adhanplayer "$POD":/adhanplayer/media/`
- Verify: `kubectl exec -n adhanplayer "$POD" -- ls -la /adhanplayer/media | head`

Test
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

### Media on PVC (local-path)

Use a PVC with the k3s local-path provisioner and copy your media into it. This keeps the image small and persists audio across rollouts.

1) Create the PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: adhanplayer-media
  namespace: adhanplayer
  annotations:
    volume.kubernetes.io/selected-node: pi48gb
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi  # adjust as needed
storageClassName: local-path
```

Apply it:

```bash
kubectl apply -f pvc.yaml   # or paste the YAML above into a file and apply
```

2) Mount PVC and rollout

The Deployment in `k8s_deployment/deployment.yaml` already mounts the PVC at `/adhanplayer/media` and sets `MEDIA_DIR`. Roll it out:

```bash
kubectl apply -f k8s_deployment/deployment.yaml
kubectl rollout status deploy/adhanplayer -n adhanplayer
```

3) Seed the media into the PVC (clear steps)

From your workstation (repo root):

```bash
# wait for the pod to be Ready (PVC must be Bound)
kubectl get pods -n adhanplayer

# get the pod name
POD=$(kubectl get po -n adhanplayer -l app=adhanplayer -o jsonpath='{.items[0].metadata.name}')

# copy local media/ into the mounted PVC path inside the pod
kubectl cp media/. -n adhanplayer "$POD":/adhanplayer/media/

# verify files exist in the pod (PVC)
kubectl exec -n adhanplayer "$POD" -- ls -la /adhanplayer/media | head
```

Notes:
- Update media later by repeating `kubectl cp`, or use an initContainer/Job as described in `docs/MEDIA_PVC.md`.
- Ensure your audio device is accessible in the pod (e.g., `--device /dev/snd` if running Docker directly; for k8s see node/device configuration).

PVC binding with local-path
- The default `local-path` StorageClass uses `volumeBindingMode: WaitForFirstConsumer`.
- A PV will be created and bound only after a Pod that mounts the PVC is scheduled (apply the Deployment first).
- This repository’s `k8s_deployment/pvc.yaml` already includes the node annotation targeting `pi48gb`:

  `metadata.annotations.volume.kubernetes.io/selected-node: pi48gb`

  Change `pi48gb` if your target node name differs.

- If you created a PVC without that annotation and it remains Pending, you can add it via patch:

```bash
kubectl patch pvc adhanplayer-media -n adhanplayer \
  -p '{"metadata":{"annotations":{"volume.kubernetes.io/selected-node":"pi48gb"}}}'
```


YAML files in `k8s_deployment/`
- `deployment.yaml`: Namespace + Deployment (container config)
- `service.yaml`: ClusterIP Service `adhanplayer` on port 8000
- `middlewares.yaml`: Traefik middlewares for `/adhanplayer` path handling
- `ingress.yaml`: Traefik Ingress exposing `http://tinker/adhanplayer`
- `pvc.yaml`: PVC `adhanplayer-media` (local-path provisioner)

Apply in order (manual):

```bash
kubectl apply -f k8s_deployment/service.yaml
kubectl apply -f k8s_deployment/middlewares.yaml
kubectl apply -f k8s_deployment/ingress.yaml
kubectl apply -f k8s_deployment/pvc.yaml
kubectl apply -f k8s_deployment/deployment.yaml
```

CI note: the current `k8s_deploy.yml` workflow applies only `deployment.yaml`. Apply the other YAMLs manually once, or update the workflow to apply them as well.

# Pre-Reqs
A Raspberry pi node cluster with networking
ensure ssh keys are configured for use across pi cluster
Need to setup k3s on the pi cluster.
use the awesome: https://github.com/alexellis/k3sup

## Reconnecting into an existing K3s/k3sup setup if the workstation is delte
* Get the k3s.yaml file from the master node. This would be in the /etc/rancher/k3s folder
* copy this file as "config" into $HOME/.kube folder
* Update config file to point to correct master node ip address or hostname
* confirm with kubectl on workstation

# Troubleshoot adhanplayer pod
Log into the adhanplayer pod  as follows :
` kubectl exec --stdin --tty adhanplayer-597b7cdd77-gszhc -n adhanplayer -- /bin/bash`

# white noise to keep blue tooth speaker alive

Created a crontab to run the sox whiteoise sync as part of the docker container to keep the bluetooth speaker from shutting off.


# text 2 speech
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
 
 
 # Github actions: k8s_deployment
 Ensure that you have the corrct kubeconfig in the secrest of the repo
 
