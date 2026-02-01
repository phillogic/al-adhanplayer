# Media on PVC: Options and Recipes

This document outlines practical ways to store and manage adhan media on a PersistentVolumeClaim (PVC) in k3s, keeping the application image small and making media updates easier.

## Goals

- Keep the runtime image slim (no baked-in media)
- Persist media across pod restarts and image updates
- Support easy one-time seeding and future updates

## App configuration

- Set `MEDIA_DIR=/adhanplayer/media` so the app reads media from the mounted PVC path.
- Do not copy `media/` into the container image.

## Recommended: PVC + `kubectl cp` (simple and fast)

1) Create a PVC (local-path on k3s)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: adhanplayer-media
  namespace: adhanplayer
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi  # adjust as needed
  storageClassName: local-path
```

2) Mount the PVC in the Deployment and set the env var

Snippet to add to `k8s_deployment/deployment.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: adhanplayer
        env:
        - name: MEDIA_DIR
          value: "/adhanplayer/media"
        volumeMounts:
        - name: media
          mountPath: /adhanplayer/media
      volumes:
      - name: media
        persistentVolumeClaim:
          claimName: adhanplayer-media
```

3) Seed the media from your workstation into the running pod

```bash
# get any running adhanplayer pod name
POD=$(kubectl get po -n adhanplayer -l app=adhanplayer -o jsonpath='{.items[0].metadata.name}')

# copy local media/ into the mounted PVC path inside the pod
kubectl cp media/. -n adhanplayer "$POD":/adhanplayer/media/

# verify
kubectl exec -n adhanplayer "$POD" -- ls -la /adhanplayer/media | head
```

Result: media persists on the PVC; image remains slim.

## Alternative 1: InitContainer seeder image (reproducible seeding)

Build a tiny image that contains only media at `/seed`, and copy into the PVC if empty.

Example `Dockerfile` (seed image):

```Dockerfile
FROM alpine:3.20
WORKDIR /seed
COPY media/ .
```

Deployment snippet to add an initContainer:

```yaml
spec:
  template:
    spec:
      initContainers:
      - name: seed-media
        image: your-registry/adhanplayer-media-seed:latest
        command: ["/bin/sh","-c"]
        args:
          - |
            set -e
            if [ -z "$(ls -A /adhanplayer/media 2>/dev/null)" ]; then
              echo "Seeding media into PVC..."
              cp -rv /seed/. /adhanplayer/media/
            else
              echo "PVC not empty; skipping seed."
            fi
        volumeMounts:
        - name: media
          mountPath: /adhanplayer/media
      containers:
      - name: adhanplayer
        volumeMounts:
        - name: media
          mountPath: /adhanplayer/media
      volumes:
      - name: media
        persistentVolumeClaim:
          claimName: adhanplayer-media
```

Pros: reproducible seeding and no manual steps. Cons: you still build a media-only image when media changes.

## Alternative 2: One-off seeding Job (download from URL/S3)

If media is hosted remotely, run a Job that mounts the PVC and downloads/unpacks into it.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: adhanplayer-media-seed
  namespace: adhanplayer
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: fetch
        image: curlimages/curl:8.7.1
        command: ["/bin/sh","-c"]
        args:
          - |
            set -eux
            # Replace with your URL; .tar.gz recommended
            URL="https://example.com/adhan-media.tar.gz"
            cd /adhanplayer/media
            curl -L "$URL" -o media.tgz
            tar xvf media.tgz --strip-components=0
            rm -f media.tgz
        volumeMounts:
        - name: media
          mountPath: /adhanplayer/media
      volumes:
      - name: media
        persistentVolumeClaim:
          claimName: adhanplayer-media
```

Run the Job once, then delete it after success.

## Alternative 3: On-node copy into local-path PV (advanced)

`local-path` storage in k3s uses hostPath under `/var/lib/rancher/k3s/storage`. You can copy media onto the node into the PV directory. This is brittle and depends on node internals; prefer the pod-based approaches above.

## Updating media later

- Use `kubectl cp` again into the same path, or
- Re-run the seeding Job, or
- Update the initContainer seed image tag and re-rollout, or
- For large/remote sets, mount object storage via a sidecar or CSI driver.

## Permissions and users

The current container runs as root, so it can write into the mounted PVC by default. If you later drop privileges, ensure the pod’s user/group has write permissions on the mount.

## Image slimming checklist

- Use `Dockerfile.slim` (Python slim base + libvlc runtime)
- Do not `COPY media/` into the image; mount via PVC
- Use `pip install --no-cache-dir` and `apt-get --no-install-recommends`
- Consider removing optional `sox`/cron if not needed

## Verification

```bash
# App sees media
curl -s http://tinker/adhanplayer/health

# Try a preview (inside cluster or via Ingress path)
curl -s "http://tinker/adhanplayer/api/v1/player/preview?prayer=fajr"
```

