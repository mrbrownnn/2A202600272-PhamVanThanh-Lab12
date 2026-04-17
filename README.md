# Lab 12 - Complete Production Agent

Du an nay tong hop day du bai Day 12: API auth, rate limit, cost guard, Docker multi-stage, Redis stateless, health/readiness, va cloud deployment.

## Features

- 12-factor config (`app/config.py`)
- API key authentication (`app/auth.py`)
- Redis-backed rate limiting (`app/rate_limiter.py`)
- Redis-backed monthly cost guard (`app/cost_guard.py`)
- Health (`/health`) + readiness (`/ready`)
- Graceful shutdown (SIGTERM)
- Multi-stage Dockerfile + non-root runtime user

## Run Local

```bash
# 1) Tao env local
cp .env.example .env

# 2) Start full stack (agent + redis)
docker compose up --build

# 3) Health check
curl http://localhost:8000/health

# 4) Auth check (khong co key -> 401)
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","question":"hello"}'

# 5) API call dung key
curl -X POST http://localhost:8000/ask \
     -H "X-API-Key: dev-key-change-me-in-production" \
     -H "Content-Type: application/json" \
     -d '{"user_id":"test","question":"Hello deployment"}'
```

## Self-Test Commands

```bash
# 1. Health
curl http://localhost:8000/health

# 2. Ready
curl http://localhost:8000/ready

# 3. Rate limiting (expect 429 after 10 req/min)
for i in {1..15}; do
     curl -X POST http://localhost:8000/ask \
          -H "X-API-Key: dev-key-change-me-in-production" \
          -H "Content-Type: application/json" \
          -d '{"user_id":"test","question":"rate test"}'
done
```

## Deploy Railway

```bash
npm i -g @railway/cli
railway login
railway init

railway variables set ENVIRONMENT=production
railway variables set OPENAI_API_KEY=sk-xxx
railway variables set AGENT_API_KEY=your-strong-key
railway variables set JWT_SECRET=your-strong-secret
railway variables set REDIS_URL=redis://default:password@host:6379
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0

railway up
railway domain
```

## Deploy Render

1. Push code len GitHub.
2. Render Dashboard -> New -> Blueprint.
3. Chon repo co file `render.yaml`.
4. Set secret env vars: `OPENAI_API_KEY`, `AGENT_API_KEY`, `JWT_SECRET`, `REDIS_URL`.
5. Deploy va lay public URL.

## Production Readiness Check

```bash
python check_production_ready.py
```
