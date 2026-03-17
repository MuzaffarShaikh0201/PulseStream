# Deployment Guide – Oracle Cloud

## Overview

- **CI**: Builds and pushes the Docker image to Docker Hub on push to `main` or `dev`
- **CD**: Deploys to your Oracle Cloud compute instance when CI succeeds on `main`

## Prerequisites

### 1. Docker Hub

1. Create a [Docker Hub](https://hub.docker.com) account
2. Create a repository (e.g. `pulsestream`)
3. Add GitHub secrets:
   - `DOCKERHUB_USERNAME` – your Docker Hub username
   - `DOCKERHUB_TOKEN` – your Docker Hub access token (Settings → Security → New Access Token)

### 2. Oracle Cloud Compute Instance (Ubuntu)

1. Create an Ubuntu VM on Oracle Cloud
2. Install Docker and Docker Compose:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # Log out and back in
   sudo apt install docker-compose-plugin
   ```
3. Create app directory:
   ```bash
   mkdir -p ~/pulsestream && cd ~/pulsestream
   ```
4. Create `.env` with all config (from Bitwarden or your secrets)
5. Ensure `docker-compose.prod.yml` is present (CD copies it on each deploy)

### 3. SSH Access

1. Generate an SSH key pair (or use existing)
2. Add the **public** key to your Oracle instance (`~/.ssh/authorized_keys`)
3. Add GitHub secrets:
   - `SSH_HOST` – Oracle instance public IP or hostname
   - `SSH_USER` – `ubuntu` (for Ubuntu instances)
   - `SSH_PRIVATE_KEY` – full contents of your private key

### 4. Optional: App Directory

If your deploy path is not `~/pulsestream`, add a GitHub variable:
- **Name**: `APP_DIR`
- **Value**: e.g. `~/myapp` or `/opt/pulsestream`

## First-Time Setup on Oracle Instance

```bash
cd ~/pulsestream
# Create .env (copy from Bitwarden or .env.example)
# docker-compose.prod.yml is copied by CD; for first run, clone the repo or copy it manually
export DOCKERHUB_IMAGE=YOUR_USERNAME/pulsestream:latest
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Private Docker Hub Images

If your image is private, add a Docker login step on the Oracle instance before the first deploy:

```bash
docker login -u YOUR_USERNAME -p YOUR_TOKEN
```

Or use a `docker login` step in the CD workflow (requires storing the token on the instance).

## Manual Deploy

Run the CD workflow manually: **Actions → CD → Run workflow**.
