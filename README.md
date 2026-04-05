# maintmode

Maintenance mode manager for Traefik v3. A single Docker container that provides:

- **Admin dashboard** to toggle maintenance mode per-site with one click
- **Styled maintenance pages** (503) served to visitors when a site is in maintenance
- **Custom error pages** (4xx/5xx) that any Traefik service can opt into

## How it works

Traefik's file provider watches a dynamic config directory. When you enable maintenance for a site, this app writes a YAML file with a high-priority router (priority 1000) that redirects all traffic for that host to the maintenance page. When you disable it, the file is deleted and Traefik reverts to the normal Docker-based router. No Traefik restart needed.

## Setup

### Prerequisites

- Traefik v3 with file provider configured:
  ```
  --providers.file.directory=/etc/traefik/dynamic
  --providers.file.watch=true
  ```
- The `proxy` Docker network exists: `docker network create proxy`

### 1. Configure the volume mount

Edit `docker-compose.yml` and set the Traefik dynamic config path:

```yaml
volumes:
  - ../traefik/dynamic:/traefik-dynamic  # Adjust to your Traefik dynamic dir
```

This must be the **same host directory** that Traefik mounts as `/etc/traefik/dynamic:ro`.

### 2. Set up authentication

```bash
# Generate a password hash
htpasswd -nB admin

# Create .env file (double the $ signs for Docker Compose)
echo 'MAINTMODE_USERS=admin:$$2y$$05$$...' > .env
```

### 3. Start

```bash
docker compose up -d --build
```

### 4. Access the dashboard

Open `https://maint.storavalla.se/admin/` and log in.

## Usage

### Maintenance mode

1. Open the admin dashboard
2. Add a site by entering its hostname and display name
3. Click **Maintenance** to enable — visitors see the maintenance page
4. Click **Restore** to bring it back online

### Custom error pages (optional)

Any Traefik service can use the custom error pages by adding the middleware:

```yaml
labels:
  - traefik.http.routers.myapp.middlewares=custom-errors@file
```

This serves styled pages for all 4xx and 5xx errors.

## API

| Method   | Endpoint                              | Description                |
|----------|---------------------------------------|----------------------------|
| `GET`    | `/api/v1/sites`                       | List all sites             |
| `POST`   | `/api/v1/sites`                       | Register a site            |
| `DELETE` | `/api/v1/sites/{hostname}`            | Remove a site              |
| `POST`   | `/api/v1/sites/{hostname}/maintenance`| Enable maintenance         |
| `DELETE` | `/api/v1/sites/{hostname}/maintenance`| Disable maintenance        |
| `GET`    | `/api/v1/health`                      | Health check               |

## Architecture

```
Browser -> Traefik -> normal service          (maintenance OFF)
                   -> maintmode container     (maintenance ON, via file-provider router)

Admin   -> maint.storavalla.se -> maintmode /admin dashboard
```
