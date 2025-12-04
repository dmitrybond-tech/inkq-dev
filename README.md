# InkQ v1.0

InkQ is a platform for connecting tattoo artists, studios, and models.

## 🚀 Project Structure

This is a full-stack application with:
- **Frontend**: Astro application in the root directory
- **Backend**: FastAPI application in `backend/` directory
- **Database**: PostgreSQL

## 🧞 Development Commands

All commands are run from the root of the project:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs frontend dependencies                    |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |

For backend development, see `backend/README.md`.

## 🐳 Docker Preprod Setup

The project includes Docker Compose configuration for preprod deployment with three services:
- **PostgreSQL** database (`inkq_preprod`)
- **FastAPI backend** on port 8000
- **Astro frontend** (static build) on port 4173

### Prerequisites

- Docker and Docker Compose installed
- PowerShell (Windows) or bash (Linux/Mac)

### Initial Setup

1. **Create environment file**:
   ```powershell
   Copy-Item .env.preprod.example .env.preprod
   ```

2. **Edit `.env.preprod`** and set the required values:
   - `POSTGRES_PASSWORD` - Strong password for the database
   - `SECRET_KEY` - Random string for session encryption
   - `BACKEND_CORS_ORIGINS` - JSON array of allowed origins (default: `["http://localhost:4173"]`)

### Running the Preprod Stack

**Start all services**:
```powershell
docker compose -f docker-compose.preprod.yml up --build
```

**Start in detached mode** (background):
```powershell
docker compose -f docker-compose.preprod.yml up --build -d
```

**View service status**:
```powershell
docker compose -f docker-compose.preprod.yml ps
```

**View logs**:
```powershell
# All services
docker compose -f docker-compose.preprod.yml logs

# Specific service
docker compose -f docker-compose.preprod.yml logs backend
docker compose -f docker-compose.preprod.yml logs frontend
docker compose -f docker-compose.preprod.yml logs db
```

**Stop services**:
```powershell
docker compose -f docker-compose.preprod.yml down
```

**Stop and remove volumes** (⚠️ deletes database data):
```powershell
docker compose -f docker-compose.preprod.yml down -v
```

### Database Initialization

After starting the services, initialize the database schema:

```powershell
docker compose -f docker-compose.preprod.yml exec backend python -m app.scripts.init_db
```

This will create all required tables. The script is idempotent and safe to run multiple times.

**Optional flags**:
- `--use-alembic` - Run Alembic migrations in addition to model-based table creation
- `--seed` - Seed demo data (creates a test artist account)
- `--echo-sql` - Enable SQL query logging

Example with Alembic:
```powershell
docker compose -f docker-compose.preprod.yml exec backend python -m app.scripts.init_db --use-alembic
```

### Accessing Services

Once running:
- **Frontend**: http://localhost:4173
- **Backend API**: http://localhost:8000
- **Database**: localhost:5434 (user: `inkq_preprod`, database: `inkq_preprod`)

The frontend is configured to call the backend via `/api` path (relative URL), which will be reverse-proxied by Caddy in production.

### Troubleshooting

**Backend won't start**:
- Check that `.env.preprod` has all required variables set
- Verify database is healthy: `docker compose -f docker-compose.preprod.yml ps db`
- Check backend logs: `docker compose -f docker-compose.preprod.yml logs backend`

**Frontend build fails**:
- Check Node version compatibility (requires Node 22+)
- Review build logs: `docker compose -f docker-compose.preprod.yml logs frontend`

**Database connection errors**:
- Ensure database container is healthy before starting backend
- Verify `POSTGRES_PASSWORD` matches in `.env.preprod`
- Check database logs: `docker compose -f docker-compose.preprod.yml logs db`

## 🔄 CI & Preprod Images

### Automated Image Builds

On every push to the `main` branch, GitHub Actions automatically:

- Builds Docker images for both backend and frontend using the existing Dockerfiles
- Pushes images to GitHub Container Registry (GHCR) with the following tags:
  - `ghcr.io/dmitrybond-tech/inkq-backend:preprod` (stable preprod tag)
  - `ghcr.io/dmitrybond-tech/inkq-backend:<GIT_SHA>` (commit-specific tag for traceability)
  - `ghcr.io/dmitrybond-tech/inkq-frontend:preprod` (stable preprod tag)
  - `ghcr.io/dmitrybond-tech/inkq-frontend:<GIT_SHA>` (commit-specific tag for traceability)

The workflow is located at `.github/workflows/build-and-push.yml` and uses the built-in `GITHUB_TOKEN` for authentication.

### Updating Preprod Deployment

To update the preprod environment on your VPS with the latest images:

1. **Pull the latest images**:
   ```powershell
   docker compose -f docker-compose.preprod.yml pull
   ```

2. **Restart services with the new images**:
   ```powershell
   docker compose -f docker-compose.preprod.yml up -d
   ```

The `docker-compose.preprod.yml` file is configured to use the `:preprod` tagged images from GHCR, so pulling and restarting will automatically use the latest images built from the main branch.

**Note**: Deployment is currently a manual step. After CI completes building and pushing images, you need to run the pull and up commands on your VPS to deploy the updates.

## 👀 Want to learn more?

- [Astro Documentation](https://docs.astro.build)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
