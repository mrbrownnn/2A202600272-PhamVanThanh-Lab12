# Deployment Information

## Public URL
- TODO: Paste your real public URL here
- Example: https://your-agent.up.railway.app

## Platform
- Railway

## Build Source
- App directory: 06-lab-complete/
- Entrypoint: app.main:app
- Health path: /health

## Required Environment Variables
- PORT
- ENVIRONMENT=production
- OPENAI_API_KEY
- AGENT_API_KEY
- JWT_SECRET
- REDIS_URL
- RATE_LIMIT_PER_MINUTE=10
- MONTHLY_BUDGET_USD=10.0
- LOG_LEVEL

## Deployment Steps (Railway)

### 1) Prepare local project
```bash
cd 06-lab-complete
cp .env.example .env
```

### 2) Install and login Railway CLI
```bash
npm i -g @railway/cli
railway login
```

### 3) Create project and link source
```bash
railway init
```

### 4) Set production variables
```bash
railway variables set ENVIRONMENT=production
railway variables set OPENAI_API_KEY=YOUR_OPENAI_KEY
railway variables set AGENT_API_KEY=YOUR_STRONG_API_KEY
railway variables set JWT_SECRET=YOUR_STRONG_JWT_SECRET
railway variables set REDIS_URL=YOUR_REDIS_URL
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0
railway variables set LOG_LEVEL=INFO
```

### 5) Deploy
```bash
railway up
railway domain
```

### 6) Copy URL
- Paste output from railway domain into Public URL section.

## Test Commands

Replace YOUR_URL and YOUR_KEY before running:

```bash
$env:YOUR_URL="https://your-agent.up.railway.app"
$env:YOUR_KEY="your-api-key"
```

### Health Check
```bash
curl $env:YOUR_URL/health
# Expected: {"status":"ok", ...}
```

### Readiness Check
```bash
curl $env:YOUR_URL/ready
# Expected: {"ready": true}
```

### API Test (with authentication)
```bash
curl -X POST $env:YOUR_URL/ask \
  -H "X-API-Key: $env:YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

### Auth Required Test
```bash
curl -X POST $env:YOUR_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
# Expected: 401
```

### Rate Limit Test
```bash
for i in {1..15}; do
  curl -X POST $env:YOUR_URL/ask \
    -H "X-API-Key: $env:YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test", "question": "rate test"}'
done
# Expected: eventually 429
```

## Actual Test Results

### Health Response
- TODO: Paste response JSON

### Readiness Response
- TODO: Paste response JSON

### Auth Test
- TODO: Paste status/output showing 401

### Valid API Test
- TODO: Paste status/output showing 200

### Rate Limit Test
- TODO: Paste output showing 429

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)

## Notes
- If using Render instead of Railway, keep test commands unchanged and only replace Public URL.
- Do not commit real secrets to Git.

## Final Submission URL
- TODO: Paste your repository URL
