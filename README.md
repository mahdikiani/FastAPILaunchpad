# FastAPI Boilerplate

This FastAPI Boilerplate is designed to provide a robust starting point for building modern web applications. It comes pre-configured with Docker, Traefik for easy deployment, and GitHub Actions for continuous integration. The boilerplate supports both SQL and NoSQL databases through flexible ORM configurations.

## Features

- **FastAPI**: High-performance, easy to learn, fast to code, ready for production
- **Docker and Docker Compose**: Containerization of the application and its dependencies for easy deployment and scaling
- **Traefik Integration**: Simplifies networking and SSL termination
- **GitHub Actions**: Automated testing and deployment
- **ORM Flexibility**: Configurable for use with various ORMs to support both SQL and NoSQL databases

## Requirements

- Docker
- Docker Compose

## Getting Started

To get started with this boilerplate, clone the repository and follow the steps below.

### 1. Clone the Repository

```bash
git clone https://github.com/mahdikiani/FastAPILaunchpad.git
cd FastAPILaunchpad
```

### 2. Environment Variables

Copy the sample environment file and customize it if needed:

```bash
cp sample.env .env
```
Update `DOMAIN` in `.env` to `localhost` for local development. Other variables like `PROJECT_NAME` can be set as per your project.

### 3. Build and Run with Docker Compose

```bash
docker-compose up --build
```

This command will build the Docker image and run the container as specified in your `docker-compose.yml` file. Your FastAPI application will be available directly at `http://localhost:8000`.

### 4. Accessing the API

Navigate to `http://localhost:8000/docs` in your web browser to view the automatic interactive API documentation provided by Swagger UI.

## Configuration

### Database Configuration

Database connection settings are managed in `app/server/config.py`. This boilerplate is designed to be flexible and can be adapted to various SQL and NoSQL databases by modifying the ORM setup and connection strings in this file. Refer to the comments and structure within `app/server/config.py` for more details on customization.

### Traefik Configuration

Traefik is optional for local development but recommended for production deployments as a reverse proxy and for managing SSL certificates.

For production, you can:
*   Create a separate `docker-compose.traefik.yml` or `traefik.yml` file that includes Traefik service definitions and the necessary labels for the `app` service.
*   Alternatively, re-integrate the Traefik labels into the main `docker-compose.yml`. The original `docker-compose.yml` (before the simplification for local development) can serve as a reference for the required labels and network configurations. You can find previous versions in the Git history.

### Debugging

The `app/Dockerfile` is configured to run the application using `CMD ["python", "app.py"]` by default. For debugging:

1.  Modify the `app/Dockerfile` to use the `debugpy` command. Comment out the current `CMD` and uncomment the one for debugging:
    ```dockerfile
    # CMD [ "python","app.py" ]
    CMD ["python", "-m" ,"debugpy", "--listen", "0.0.0.0:3000", "-m", "app"]
    ```
2.  Rebuild the Docker image:
    ```bash
    docker-compose build app
    ```
    Or, if you prefer to rebuild and restart:
    ```bash
    docker-compose up --build
    ```
3.  Configure your IDE to attach to the debugger on port `3000`.

## Running without Docker (Optional)

While Docker is the recommended method for consistency and ease of deployment, you can also run the application locally without it:

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r app/requirements.txt
    ```
3.  **Set up environment variables:**
    The application may rely on environment variables defined in `.env`. Ensure these are available in your shell. You can manually create a `.env` file (if you haven't already from the Docker setup) and load it using a library like `python-dotenv` if you modify `app/app.py` or manage them through your shell. For example, your `.env` could look like:
    ```
    PROJECT_NAME=my_project
    DOMAIN=localhost
    TESTING=false
    # Add other necessary variables
    ```
4.  **Run the application:**
    ```bash
    python app/app.py
    ```
    The application should be available at `http://localhost:8000`.

**Note:** Using Docker is highly recommended to ensure a consistent environment across development, testing, and production.

### Continuous Integration

GitHub Actions workflows are set up for continuous integration, ensuring that your tests run automatically every time you push changes to your repository.

### License

This project is licensed under the [MIT License](https://github.com/mahdikiani/FastAPILaunchpad/blob/main/LICENSE).
