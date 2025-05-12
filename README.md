# 📁 Django File Sharing System

A secure, scalable file-sharing system built with Django, PostgreSQL, Redis, Celery, and AWS S3 — fully Dockerized.

---

## 🚀 Features

- User authentication (JWT + Google OAuth)
- Upload & version files
- Scan files asynchronously using Celery
- Share files publicly or with specific users
- Track file access logs
- Search with Elasticsearch
- Store files in AWS S3 (or local storage)
- Membership plans using Stripe Checkout
- Docker + Docker Compose support

---

## 🛠 Tech Stack

- Django 4.x
- PostgreSQL 14
- Celery + Redis
- Stripe Payments
- Elasticsearch
- AWS S3 (via `boto3`)
- Docker & Docker Compose
- Flower (for monitoring Celery tasks)

---

## 🧰 Prerequisites

Make sure you have:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- An AWS S3 bucket (optional)
- Redis and Elasticsearch running locally or in containers

---

## 📁 Project Structure

```

project/
├── app/                  # Django app
├── Project/              # Django project settings
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── .env
└── README.md

````


## 🚀 Running the Project

### 1. Build and Start Containers

```bash
docker-compose build
docker-compose up
```

### 2. Access Services

* Django App: [http://localhost:8000](http://localhost:8000)
* Flower (Celery Monitor): [http://localhost:5555](http://localhost:5555)

---

## 🧪 Common Commands

### Run Django commands inside the container

```bash
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py makemigrations
```

### Rebuild the project

```bash
docker-compose down
docker-compose build
docker-compose up
```
