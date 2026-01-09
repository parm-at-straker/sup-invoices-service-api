# Invoice/Purchase Order Service API

Microservice for managing invoices and purchase orders in the Straker translation platform.

This service provides REST API endpoints for:
- Invoice management (CRUD operations, approval, payment tracking)
- Purchase Order management (CRUD operations, approval workflow, payment processing)
- Financial reporting and operations

This repository is based on the Straker FastAPI template and includes features common in many of Straker's FastAPI apps, such as:

- Environment management
- App configuration
- Health check endpoint
- SQL database
- Redis
- BugLog
- Elastic APM
- Docker containerization

Be familiar with these Python libraries to develop using this template effectively:

- [FastAPI](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic](https://docs.pydantic.dev/latest/concepts/models/)
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

## Instructions

To run the app:

1. Create a `.env` file from `.env.local` (or `.env.example`) and fill in the remaining environment variables if required:

   ```sh
   $ cp .env.local .env
   ```

2. Set up the required environment variables. The service requires database connection settings for both `franchise` and `sitemanager` databases:

   ```bash
   # Environment
   ENVIRONMENT=local

   # Database - Franchise (primary)
   DB_HOST_franchise=localhost
   DB_PORT_franchise=3306
   DB_USER_franchise=root
   DB_PASSWORD_franchise=your_password

   # Database - Franchise Read-only
   DB_HOST_franchise_readonly=localhost
   DB_PORT_franchise_readonly=3306
   DB_USER_franchise_readonly=root
   DB_PASSWORD_franchise_readonly=your_password

   # Database - Sitemanager (if needed)
   DB_HOST_sitemanager=localhost
   DB_PORT_sitemanager=3306
   DB_USER_sitemanager=root
   DB_PASSWORD_sitemanager=your_password

   # Database - Sitemanager Read-only
   DB_HOST_sitemanager_readonly=localhost
   DB_PORT_sitemanager_readonly=3306
   DB_USER_sitemanager_readonly=root
   DB_PASSWORD_sitemanager_readonly=your_password

   # Optional: Health check password (required in production)
   HEALTH_CHECK_PASSWORD=

   # Optional: Elastic APM
   ELASTIC_APM_SERVER_URL=
   ```

3. Install the dependencies listed in `Pipfile`:

   ```sh
   $ pipenv sync --dev
   ```

4. Run the app:

   ```sh
   $ pipenv run uvicorn src.main:app --reload --port 12345
   ```

## API Endpoints

### Invoices

- `GET /v1/invoices` - List invoices with filtering and pagination
- `GET /v1/invoices/{uuid}` - Get invoice by UUID
- `POST /v1/invoices` - Create new invoice
- `PUT /v1/invoices/{uuid}` - Update invoice
- `DELETE /v1/invoices/{uuid}` - Delete invoice (soft delete)
- `POST /v1/invoices/{uuid}/approve` - Approve invoice

### Purchase Orders

- `GET /v1/purchase-orders` - List purchase orders with filtering and pagination
- `GET /v1/purchase-orders/{uuid}` - Get purchase order by UUID
- `POST /v1/purchase-orders` - Create new purchase order
- `PUT /v1/purchase-orders/{uuid}` - Update purchase order
- `DELETE /v1/purchase-orders/{uuid}` - Delete purchase order (soft delete)
- `POST /v1/purchase-orders/{uuid}/approve` - Approve purchase order for payment

See `/docs` endpoint for interactive API documentation when running in non-production environments.

## Quick Start

1. **Install dependencies**:
   ```bash
   pipenv sync --dev
   ```

2. **Create `.env` file** with database connection settings (see [Environment Variables](#environment-variables) below)

3. **Run the service**:
   ```bash
   pipenv run uvicorn src.main:app --reload --port 12345
   ```

4. **Access the API**:
   - API Documentation: http://localhost:12345/docs
   - Health Check: http://localhost:12345/health

For detailed setup instructions, see [docs/RUNNING_THE_SERVICE.md](docs/RUNNING_THE_SERVICE.md).

## Environment Variables

The service requires the following environment variables to be set in a `.env` file:

```bash
# Required
ENVIRONMENT=local

# Database - Franchise (primary)
DB_HOST_franchise=localhost
DB_PORT_franchise=3306
DB_USER_franchise=root
DB_PASSWORD_franchise=your_password

# Database - Franchise Read-only
DB_HOST_franchise_readonly=localhost
DB_PORT_franchise_readonly=3306
DB_USER_franchise_readonly=root
DB_PASSWORD_franchise_readonly=your_password

# Database - Sitemanager (if needed)
DB_HOST_sitemanager=localhost
DB_PORT_sitemanager=3306
DB_USER_sitemanager=root
DB_PASSWORD_sitemanager=your_password

# Database - Sitemanager Read-only
DB_HOST_sitemanager_readonly=localhost
DB_PORT_sitemanager_readonly=3306
DB_USER_sitemanager_readonly=root
DB_PASSWORD_sitemanager_readonly=your_password

# Optional
HEALTH_CHECK_PASSWORD=
ELASTIC_APM_SERVER_URL=
```

**Note**: The `DBEnginePool` from `straker_utils` expects environment variables in the format `DB_HOST_{database_name}`, `DB_PORT_{database_name}`, etc.

## Directory Structure

- `.vscode`
  - `settings.json` contains the VS Code workplace settings. This will make VS Code automatically format your code when saving files.
  - `extensions.json` contains the recommended VS Code extensions for the project. A message will appear upon opening this repo in VS Code if some recommended extensions are not installed yet.
- `src`
  - This directory contains the main Python source code of this app. The `main.py` file is the entrypoint of this app and is called by `uvicorn` to start the web server.
  - The directory structure is loosely based on this [FastAPI Best Practices article](https://github.com/zhanymkanov/fastapi-best-practices). Each "section" of the API is located in their own subdirectory in the `src` directory. It is a good idea to read the rest of the article.
- `tests`
  - This template uses [pytest](https://docs.pytest.org/en/latest/) for unit testing. View [FastAPI's testing guide](https://fastapi.tiangolo.com/tutorial/testing/) to learn how to test endpoints.
- `.editorconfig`
  - Config file for [EditorConfig](https://editorconfig.org/), used to format files. Install the [EditorConfig for VS Code](vscode:extension/EditorConfig.EditorConfig) extension to format files automatically.
- `.env.example`
  - Contains all the environment variables required for this app to work. Create a `.env` file based on this file and fill in the values to be able run this app. As good practice, `.env` will not be commited to the repository. DevOps will write in the appropriate values when deploying this app..
- `.env.local`
  - Same as `.env.example`, but with suggested values for local development. Ideally, a developer would be able to duplicate this file and rename it as `.env` to configure most or all of the environment variables. **Do not write passwords or other sensitive information here as they should not be commited to the repository!**
- `build.jenkinsfile`
  - Used by DevOps to configure the [Jenkins](https://mgmt-k8s-jenkins-fra02.straker.io/) CI/CD pipeline.
- `docker-compose.yml`

  - Docker Compose config file to help create a local Docker container of this app. A local container can be built with:

    ```sh
    $ docker compose up -d --build
    ```

- `Dockerfile`
  - Configuration file for Docker containerization. Read this file to understand how this app is deployed to production.
- `Pipfile`
  - The list of dependencies required to run the app. This is similar to `package.json` for NPM. [Pipenv](https://pipenv.pypa.io/en/latest/pipfile.html) is used to manage the project dependencies.
- `Pipfile.lock`
  - The lock file for Pipenv. This is similar to `package-lock.json` for NPM. Changes to this file should be committed along with `Pipfile`.
- `pyproject.toml`
  - Contains the configuration for [Ruff](https://docs.astral.sh/ruff/) (linter/formatter) and [mypy](https://mypy.readthedocs.io/en/stable/) (type checker).

## Additional Features

The following features will be added to this template or documented elsewhere in the future.

- Ratelimiting
- Authentication
- Authorization (permissions)
- OpenAPI
