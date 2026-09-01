# 🇩🇪 German Exercises App

**Interactive educational platform for German language learning.**  
A full-stack web application featuring grammar exercises, vocabulary drills, and progress tracking, built with a strong focus on **DevSecOps practices**, **test coverage**, and **clean architecture**.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4-emerald?logo=vue.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![CI/CD](https://github.com/Vsirotkin/german-exercises-app/actions/workflows/ci.yml/badge.svg)
![Security](https://img.shields.io/badge/security-A%2B-brightgreen)

---

## ✨ Key Features

- **Smart Progression System:** Exercises are dynamically locked/unlocked based on student performance (e.g., scoring <50% triggers a review state).
- **Interactive UI:** Real-time vocabulary drills and gap-fill exercises with instant feedback.
- **Secure by Design:** JWT authentication, non-root Docker containers, and automated secret scanning.
- **Test-Driven:** Comprehensive test suites for both backend (Django) and frontend (Vitest).

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.13, Django 5.2, Django REST Framework, SimpleJWT, `uv` (package manager) |
| **Frontend** | Vue 3, Vite 7, Vue Router, Axios, Bootstrap 5 |
| **Database** | PostgreSQL 17 |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **Security** | Gitleaks, Trivy, Syft (CycloneDX SBOM) |
| **Testing** | Django TestCase, Vitest, @vue/test-utils, jsdom |

---

## 🛡️ DevSecOps & Security

This project implements industry-standard security practices:

- 🔍 **Gitleaks:** Automated scanning for hardcoded secrets and credentials in the CI pipeline.
- 🐛 **Trivy:** Vulnerability scanning for Docker images and filesystem dependencies (CVE detection).
-  **Syft:** Automated generation of Software Bill of Materials (SBOM) in CycloneDX format.
- 🔒 **Non-Root Containers:** All Docker containers run as non-root users (UID 1000) to minimize attack surface.
-  **Multi-stage Builds:** Production Dockerfiles are optimized to exclude build tools and node_modules.

---

## 🏗️ Architecture

```text
german-exercises-app/
├── backend/          # Django REST API, models, serializers, tests
├── frontend/         # Vue 3 SPA, components, Vitest tests
├── .github/workflows # CI (Tests) and Security pipelines
├── compose.yml       # Docker Compose orchestration
└── README.md
```

---

## 🚀 How to Run Locally

### Prerequisites
- Docker & Docker Compose
- (Optional) `uv` for backend, `npm` for frontend (for local dev without Docker)

### Using Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/Vsirotkin/german-exercises-app.git
cd german-exercises-app

# Copy environment template
cp backend/.env.example backend/.env

# Start all services
docker compose up --build
```

**Access:**
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Database:** localhost:5432

### Running Tests
```bash
# Backend tests
cd backend && make test

# Frontend tests
cd frontend && npm test -- --run
```

---

## 📜 License
MIT License. See [LICENSE](LICENSE) for details.

---
*Built with ❤️ for learning German and mastering modern web development.*
```
