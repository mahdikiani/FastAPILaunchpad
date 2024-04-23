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

### 2. Build and Run with Docker Compose

```bash
docker-compose up --build
```

This command will build the Docker image and run the containers as specified in your `docker-compose.yml` file. Your FastAPI application will be available at `http://localhost:8000`.

### 3. Accessing the API

Navigate to `http://localhost:8000/docs` in your web browser to view the automatic interactive API documentation provided by Swagger UI.

## Configuration

### Database Configuration

You can configure your database connection in the `config.py` file. This boilerplate is compatible with various ORMs and supports both SQL and NoSQL options.

### Traefik Configuration

To deploy with Traefik, ensure you have Traefik set up on your deployment server or environment. Modify the `traefik.yml` file according to your specific deployment requirements.

### Continuous Integration

GitHub Actions workflows are set up for continuous integration, ensuring that your tests run automatically every time you push changes to your repository.

### License

This project is licensed under the [MIT License](https://github.com/mahdikiani/FastAPILaunchpad/blob/main/LICENSE).
