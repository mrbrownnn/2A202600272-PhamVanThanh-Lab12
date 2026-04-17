# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secrets in source code are unsafe and non-rotatable.
2. Missing authentication allows unauthorized API usage.
3. No rate limiting can lead to abuse and denial of service.
4. No cost guard can cause uncontrolled model spend.
5. Single-process in-memory state is not stateless and does not scale.
6. No health/readiness probes makes orchestration unstable.
7. Missing graceful shutdown risks dropped requests during deploy.
8. Using root container user increases security risk.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded / local defaults | Environment variables (12-factor) | Safe, portable, reproducible deploys |
| Security | Often open endpoints | API key auth + security headers | Prevent unauthorized access |
| Rate limit | Optional or in-memory | Redis-backed policy | Stable service under load |
| Cost control | Not enforced | Monthly budget guard | Prevent cloud bill spikes |
| State | Local memory | Stateless app + Redis | Horizontal scaling |
| Observability | Basic logs | Structured JSON logs | Better operations and debugging |
| Availability | Manual restart | Health/readiness + restart policy | Better uptime |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11-slim`
2. Working directory: `/build` in builder, `/app` in runtime
3. Multi-stage: yes (`builder` and `runtime` stages)
4. Runtime user: non-root (`agent`)
5. Health check: yes (`/health` endpoint)

### Exercise 2.3: Image size comparison
- Develop: Pending measurement (run `docker images`)
- Production: Pending measurement (run `docker images`)
- Difference: Production image is smaller due to multi-stage and slim runtime

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Platform config: `06-lab-complete/railway.toml`
- Required vars: `OPENAI_API_KEY`, `AGENT_API_KEY`, `JWT_SECRET`, `REDIS_URL`, `RATE_LIMIT_PER_MINUTE`, `MONTHLY_BUDGET_USD`
- URL: Fill after deploy (use `railway domain`)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- Missing API key on `POST /ask` returns `401`.
- Valid API key on `POST /ask` returns `200` with model answer.
- Rate limiting triggers `429` after 10 requests/minute per user/key bucket.

### Exercise 4.4: Cost guard implementation
- Implemented in `06-lab-complete/app/cost_guard.py`.
- Token cost is estimated for input/output and accumulated by month.
- Budget threshold: `MONTHLY_BUDGET_USD=10.0`.
- Store uses Redis for cross-instance consistency (fallback to in-memory local mode).

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- Stateless design via Redis-backed rate limiter and cost guard.
- Liveness endpoint: `GET /health`.
- Readiness endpoint: `GET /ready`.
- Graceful shutdown handles `SIGTERM`.
- Docker compose includes app + Redis with health checks.

## Evidence Pointers

- Main app: `06-lab-complete/app/main.py`
- Auth: `06-lab-complete/app/auth.py`
- Rate limiter: `06-lab-complete/app/rate_limiter.py`
- Cost guard: `06-lab-complete/app/cost_guard.py`
- Dockerfile: `06-lab-complete/Dockerfile`
- Compose: `06-lab-complete/docker-compose.yml`
