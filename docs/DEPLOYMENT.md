# Deployment Guide

Complete guide for deploying the AI Concierge Platform to production.

## Prerequisites

- [ ] Supabase account with project created
- [ ] Railway account
- [ ] Vercel account
- [ ] Anthropic API key
- [ ] (Optional) Slack workspace and app credentials
- [ ] (Optional) AWS account for SES
- [ ] Domain name (optional but recommended)

## Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization and set project name
4. Generate a secure database password
5. Select region closest to your users
6. Wait for project to provision (~2 minutes)

### 1.2 Deploy Schema

```bash
# Get connection string from Supabase dashboard
# Project Settings > Database > Connection String > URI

psql "<your-connection-string>" -f database/schema_mvp.sql
```

### 1.3 Enable Extensions

In Supabase SQL Editor, run:

```sql
-- Enable pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 1.4 Collect Credentials

From Supabase dashboard, save these values:
- Project URL (Settings > API > Project URL)
- Service Role Key (Settings > API > service_role key)
- Anon Key (Settings > API > anon key)
- Connection String (Settings > Database > Connection String)

## Step 2: Backend Deployment (Railway)

### 2.1 Connect Repository

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your repository
5. Select your repository

### 2.2 Configure Build

Railway should auto-detect Python. If not:

1. Click on service
2. Settings > Build
3. Root Directory: `/backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2.3 Add Environment Variables

In Railway dashboard, go to Variables tab and add:

```bash
# Database
DATABASE_URL=<supabase-connection-string>
SUPABASE_URL=<supabase-project-url>
SUPABASE_SERVICE_KEY=<supabase-service-key>
SUPABASE_ANON_KEY=<supabase-anon-key>

# Anthropic AI
ANTHROPIC_API_KEY=<your-anthropic-api-key>
ANTHROPIC_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=4096

# Application
APP_URL=https://<your-railway-domain>.railway.app
FRONTEND_URL=https://<your-vercel-domain>.vercel.app
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENVIRONMENT=production
DEBUG=false

# Slack (Optional)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# AWS SES (Optional)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
SES_EMAIL=concierge@yourdomain.com

# Redis (Optional - for caching)
REDIS_URL=redis://...

# OpenAI (Optional - for embeddings)
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

### 2.4 Generate Secret Key

```bash
openssl rand -hex 32
```

### 2.5 Deploy

1. Click "Deploy"
2. Railway will build and deploy automatically
3. Wait for deployment to complete
4. Copy the generated URL (e.g., `https://athena-concierge-production.up.railway.app`)

### 2.6 Verify Deployment

Test the health endpoint:

```bash
curl https://<your-railway-url>/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

### 2.7 Set Up Workers (Background Jobs)

For the reminder worker, add a new service in Railway:

1. New > Service from GitHub repo
2. Same repository
3. Settings > Build
4. Start Command: `python -m app.workers.reminder_worker`
5. Add same environment variables

## Step 3: Frontend Deployment (Vercel)

### 3.1 Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your Git repository
4. Vercel will detect Next.js automatically

### 3.2 Configure Build

- Framework Preset: Next.js
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

### 3.3 Add Environment Variables

In Vercel dashboard, add:

```bash
NEXT_PUBLIC_API_URL=https://<your-railway-backend-url>
```

### 3.4 Deploy

1. Click "Deploy"
2. Wait for build to complete (~2-3 minutes)
3. Vercel will provide a URL (e.g., `https://athena-concierge.vercel.app`)

### 3.5 Update Backend CORS

Go back to Railway and update `FRONTEND_URL` variable to match your Vercel URL.

### 3.6 Verify Deployment

1. Visit your Vercel URL
2. Check that API health check shows "healthy"
3. Try navigating different pages

## Step 4: Custom Domain (Optional)

### 4.1 Backend Domain (Railway)

1. Railway dashboard > Settings > Networking
2. Click "Generate Domain" or add custom domain
3. If using custom domain, add DNS records:
   - Type: CNAME
   - Name: api (or subdomain of choice)
   - Value: `<your-project>.railway.app`

### 4.2 Frontend Domain (Vercel)

1. Vercel dashboard > Settings > Domains
2. Add your domain
3. Configure DNS records as instructed by Vercel

## Step 5: Slack Integration (Optional)

### 5.1 Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name: "Athena Concierge"
5. Select your workspace

### 5.2 Configure App

#### OAuth & Permissions

Add Bot Token Scopes:
- `chat:write`
- `im:read`
- `im:write`
- `im:history`
- `users:read`
- `users:read.email`

Install app to workspace and copy Bot User OAuth Token.

#### Socket Mode

1. Settings > Socket Mode > Enable
2. Generate App-Level Token with `connections:write` scope
3. Copy token

#### Event Subscriptions

Enable Events and subscribe to:
- `message.im` (Direct messages)
- `app_mention` (Mentions)

### 5.3 Update Environment Variables

Add to Railway:
```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=<from-basic-info>
```

Redeploy backend.

### 5.4 Start Slack Integration

The Slack integration should start automatically with the backend.

Check logs in Railway:
```
Starting Slack Socket Mode handler
```

## Step 6: Email Integration (SES)

### 6.1 Set Up SES

1. AWS Console > Amazon SES
2. Verify your domain or email address
3. Request production access (by default, SES is in sandbox mode)
4. Create IAM user with SES permissions
5. Generate access keys

### 6.2 Configure Receiving

1. SES > Email Receiving > Rule Sets
2. Create receipt rule
3. Add action: S3 (store emails in bucket)
4. Add action: SNS (notify your backend)

### 6.3 Set Up SNS Webhook

1. Create SNS topic
2. Create subscription with HTTPS endpoint:
   - Endpoint: `https://<your-backend>/api/v1/webhooks/ses/inbound`
3. Confirm subscription (automatically handled by backend)

### 6.4 Update Environment Variables

Add to Railway:
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
SES_EMAIL=concierge@yourdomain.com
```

## Step 7: Monitoring & Logging

### 7.1 Set Up Sentry (Optional)

1. Create Sentry account
2. Add Sentry SDK to backend:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn="<your-dsn>")
   ```

### 7.2 Enable Railway Logs

Railway automatically captures logs. View them in:
- Dashboard > Deployments > View Logs

### 7.3 Set Up Alerts

Configure alerts in Railway:
- Settings > Observability
- Add email for deployment notifications

## Step 8: Post-Deployment

### 8.1 Seed Initial Data

```bash
# Connect to production database
psql "<production-connection-string>"

# Create default organization
INSERT INTO organizations (org_id, name, domain)
VALUES ('YOUR-ORG-ID-HERE', 'Your Family Office', 'yourdomain.com');

# Create admin account
INSERT INTO accounts (org_id, email, full_name, account_type)
VALUES ('YOUR-ORG-ID-HERE', 'admin@yourdomain.com', 'Admin User', 'admin');
```

### 8.2 Test End-to-End

1. Create test client in dashboard
2. Add communication identity (email or Slack)
3. Send test message
4. Verify AI response
5. Check database records

### 8.3 Performance Testing

```bash
# Load test with 100 concurrent users
locust -f backend/tests/load_test.py \
  --host=https://<your-backend-url> \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql "<your-connection-string>" -c "SELECT 1"

# Check Railway logs
railway logs
```

### Backend Not Starting

1. Check Railway logs for errors
2. Verify all environment variables are set
3. Test locally first with production environment variables

### CORS Errors

1. Verify `FRONTEND_URL` in Railway matches Vercel URL exactly
2. Check for trailing slashes
3. Redeploy backend after changes

### Slack Not Responding

1. Check Socket Mode is enabled
2. Verify tokens are correct
3. Check Railway logs for connection errors
4. Ensure worker process is running

### Email Not Working

1. Verify SES is out of sandbox mode
2. Check SNS subscription is confirmed
3. Verify webhook endpoint is accessible
4. Check S3 bucket permissions

## Rollback Procedure

### Backend Rollback

1. Railway dashboard > Deployments
2. Find previous successful deployment
3. Click "Redeploy"

### Frontend Rollback

1. Vercel dashboard > Deployments
2. Find previous deployment
3. Click "⋯" > "Promote to Production"

### Database Rollback

```bash
# If using migrations
alembic downgrade -1

# Or restore from backup
# Supabase: Project Settings > Database > Backups
```

## Maintenance

### Backup Schedule

- Database: Automatic daily backups (Supabase)
- Configuration: Keep `.env` files in secure location
- Code: Git repository is source of truth

### Update Procedure

1. Create feature branch
2. Deploy to staging (separate Railway/Vercel projects)
3. Test thoroughly
4. Merge to main
5. Auto-deploy to production
6. Monitor logs and metrics

### Scaling

#### Backend Scaling (Railway)

- Settings > Resources
- Adjust CPU and Memory based on usage

#### Database Scaling (Supabase)

- Project Settings > Database
- Upgrade to Pro plan for more resources
- Enable connection pooling

#### Frontend Scaling (Vercel)

- Automatic edge caching and scaling
- No manual configuration needed

---

## Deployment Checklist

- [ ] Supabase project created and schema deployed
- [ ] Railway backend deployed with all environment variables
- [ ] Vercel frontend deployed and connected to backend
- [ ] Custom domains configured (if applicable)
- [ ] Slack integration tested (if enabled)
- [ ] SES integration tested (if enabled)
- [ ] Initial data seeded
- [ ] End-to-end testing completed
- [ ] Monitoring and alerts configured
- [ ] Backup strategy verified
- [ ] Documentation updated

---

Need help? Check the main README or create an issue on GitHub.
