# GitHub CI/CD Deploy

The repository includes `.github/workflows/deploy.yml`.

It deploys on every push to `main` and can also be started manually from GitHub Actions.

## Required GitHub Secrets

Set these in:

```text
GitHub repo -> Settings -> Secrets and variables -> Actions -> New repository secret
```

Required secrets:

```text
VPS_HOST
VPS_USER
VPS_SSH_KEY
VPS_PROJECT_PATH
```

Example values:

```text
VPS_HOST=123.123.123.123
VPS_USER=root
VPS_PROJECT_PATH=/opt/Arvexo-Account
```

`VPS_SSH_KEY` must be the private key that can connect to the VPS user.

## First VPS Setup

Run once on the VPS:

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker
cd /opt
git clone https://github.com/YOUR_USERNAME/Arvexo-Account.git
cd Arvexo-Account
cp .env.example .env
nano .env
docker compose up -d --build
```

For production, set at least:

```env
APP_ENV=production
JWT_SECRET=replace_with_long_random_secret
PUBLIC_SITE_URL=https://account.arvexo.ru
PUBLIC_API_URL=https://api.account.arvexo.ru
FRONTEND_URL=https://account.arvexo.ru
COOKIE_DOMAIN=.account.arvexo.ru
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
NEXT_PUBLIC_API_URL=/api
```

## What The Workflow Does

On deploy, GitHub Actions connects over SSH and runs:

```bash
cd "$VPS_PROJECT_PATH"
git fetch origin main
git reset --hard origin/main
docker compose pull postgres redis nginx || true
docker compose up -d --build
docker compose ps
```

The workflow does not store secrets in the repository.
