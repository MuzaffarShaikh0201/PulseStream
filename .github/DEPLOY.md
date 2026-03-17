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

### 1b. Bitwarden (for .env)

CD fetches config from Bitwarden and deploys `.env` automatically. Add GitHub secrets (see `.github/BITWARDEN_SETUP.md`):
- `BW_ACCESS_TOKEN` – Bitwarden machine account token
- `BW_SECRET_ID_CONFIG` – UUID of the `pulsestream-config` secret

Use production values in Bitwarden (e.g. `ENVIRONMENT=production`, prod DB password).

### 2. Oracle Cloud Compute Instance (Ubuntu)

1. Create an Ubuntu VM on Oracle Cloud
2. Install Docker and Docker Compose:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # Log out and back in (or reboot) so the docker group takes effect
   sudo apt install docker-compose
   sudo systemctl enable docker && sudo systemctl start docker
   ```
3. Ensure the SSH user is in the `docker` group (CD runs non-interactively; `sg docker` is used so Docker commands work):
   ```bash
   groups $USER   # should include docker
   ```
4. Create app directory (replace `ubuntu` with your SSH_USER if different):
   ```bash
   mkdir -p /home/ubuntu/pulsestream && cd /home/ubuntu/pulsestream
   ```
5. `docker-compose.prod.yml` and `.env` are copied by CD on each deploy (`.env` is generated from Bitwarden)

### 3. SSH Access

1. Generate an SSH key pair (or use existing)
2. Add the **public** key to your Oracle instance (`~/.ssh/authorized_keys`)
3. Add GitHub secrets:
   - `SSH_HOST` – Oracle instance public IP or hostname
   - `SSH_USER` – `ubuntu` (for Ubuntu instances)
   - `SSH_PRIVATE_KEY` – full contents of your private key
   - `SSH_KEY_PASSPHRASE` – (optional) passphrase if your key is protected

### 4. Optional: App Directory

APP_DIR defaults to `/home/{SSH_USER}/pulsestream`. To override, add a GitHub variable:
- **Name**: `APP_DIR`
- **Value**: e.g. `/home/ubuntu/myapp` or `/opt/pulsestream` (use absolute path)

## First-Time Setup on Oracle Instance

```bash
cd /home/ubuntu/pulsestream   # or /home/$SSH_USER/pulsestream

# 1. Ensure Docker is running and your user is in the docker group
sudo systemctl status docker
groups $USER   # should include docker

# 2. Create the app directory (CD will copy docker-compose.prod.yml and .env on deploy)
mkdir -p /home/ubuntu/pulsestream
```

No manual `.env` creation needed – CD pulls config from Bitwarden and deploys it automatically.

## Private Docker Hub Images

If your image is private, add a Docker login step on the Oracle instance before the first deploy:

```bash
docker login -u YOUR_USERNAME -p YOUR_TOKEN
```

Or use a `docker login` step in the CD workflow (requires storing the token on the instance).

## Manual Deploy

Run the CD workflow manually: **Actions → CD → Run workflow**.
