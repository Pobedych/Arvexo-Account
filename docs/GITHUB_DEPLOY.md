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

The matching public key must be present on the VPS in the selected user's
`~/.ssh/authorized_keys`.

## First VPS Setup

Run once on the VPS:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
mkdir -p /opt/Arvexo-Account
cd /opt/Arvexo-Account
cp .env.example .env
nano .env
docker compose up -d --build
```

If `.env.example` is not on the server yet, run the GitHub Actions deploy once,
then create `/opt/Arvexo-Account/.env` from the uploaded `.env.example`.

## Fix SSH Permission Denied

If GitHub Actions fails with:

```text
Permission denied (publickey,password)
```

the deploy key is not accepted by the VPS. Check these items:

1. `VPS_USER` is the exact Linux user that owns the deploy access, for example `root` or `deploy`.
2. `VPS_SSH_KEY` contains the private key, including the full header and footer:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

3. The matching public key is installed on the VPS:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

4. Test the same key locally before retrying GitHub Actions:

```bash
ssh -i ~/.ssh/arvexo_account_deploy -o IdentitiesOnly=yes USER@HOST
```

5. If you need a fresh deploy key, create it locally:

```bash
ssh-keygen -t ed25519 -C "arvexo-account-deploy" -f ~/.ssh/arvexo_account_deploy
```

Put `~/.ssh/arvexo_account_deploy.pub` into the VPS user's
`~/.ssh/authorized_keys`, and put the full contents of
`~/.ssh/arvexo_account_deploy` into GitHub secret `VPS_SSH_KEY`.

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

On deploy, GitHub Actions packages the checked-out repository, uploads it to the
VPS over SSH, and runs:

```bash
cd "$VPS_PROJECT_PATH"
test -f .env || cp .env.example .env
docker compose pull postgres redis nginx || true
docker compose up -d --build
docker compose ps
```

The VPS does not need to be a git clone and does not need GitHub repository
access.

The workflow does not store secrets in the repository.
