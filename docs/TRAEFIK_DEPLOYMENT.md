# WFC REST API - Traefik Production Deployment

Complete production deployment guide with Traefik reverse proxy, automatic HTTPS, load balancing, and observability.

## Features

✅ **Automatic HTTPS** - Let's Encrypt integration
✅ **Load Balancing** - 2 WFC API instances with health checks
✅ **Zero-downtime deploys** - Rolling updates with start-first strategy
✅ **Rate Limiting** - 100 req/s per IP (Traefik layer + TokenBucket)
✅ **Security Headers** - HSTS, SSL redirect, security best practices
✅ **Observability** - Prometheus metrics + Grafana dashboards
✅ **Access Logs** - Request tracing and audit trails

## Architecture

```
Internet
    ↓
Traefik (ports 80, 443, 9950)
    ├── HTTPS (443) → api.wfc.example.com → Load Balancer
    ├── HTTP (80) → Redirect to HTTPS
    └── Direct (9950) → Load Balancer
            ↓
    ┌───────┴────────┐
    ↓                ↓
WFC API #1      WFC API #2
(port 8000)     (port 8000)
    ↓                ↓
Shared Volume (~/.wfc/)
```

## Quick Start

### 1. Configure Domain (Production)

Update `docker-compose.traefik.yml`:

```yaml
# Line 25: Set your email for Let's Encrypt
- "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"

# Line 68: Set your domain
- "traefik.http.routers.wfc-api-secure.rule=Host(`api.wfc.example.com`)"
```

### 2. Start Services

```bash
# Production (with HTTPS)
docker compose -f docker-compose.traefik.yml up -d

# Development (localhost, no HTTPS)
docker compose -f docker-compose.traefik.yml up -d --scale wfc-rest-api=1
```

### 3. Verify Deployment

```bash
# Health check (direct access)
curl http://localhost:9950/

# HTTPS (production domain)
curl https://api.wfc.example.com/

# Check Traefik dashboard
open http://localhost:8080/dashboard/
```

## Access Methods

### Method 1: HTTPS with Domain (Production)

```bash
# Create project
curl -X POST https://api.wfc.example.com/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"project_id": "my-project", "developer_id": "alice", "repo_path": "/path/to/repo"}'

# Submit review
curl -X POST https://api.wfc.example.com/v1/reviews/ \
  -H "X-Project-ID: my-project" \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{"diff_content": "...", "files": ["file.py"]}'
```

### Method 2: Direct Access on Port 9950 (No Domain Required)

```bash
# Works without DNS/domain setup
curl -X POST http://localhost:9950/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"project_id": "my-project", "developer_id": "alice", "repo_path": "/path/to/repo"}'
```

### Method 3: Docker Network (Internal)

```bash
# From another container in wfc-network
curl http://wfc-rest-api:8000/v1/projects/
```

## Configuration

### Environment Variables

Create `.env` file:

```env
# Domain configuration
WFC_DOMAIN=api.wfc.example.com
ACME_EMAIL=your-email@example.com

# Rate limiting
TRAEFIK_RATE_LIMIT_AVG=100
TRAEFIK_RATE_LIMIT_BURST=50

# API instances
WFC_API_REPLICAS=2

# Logging
LOG_LEVEL=info
TRAEFIK_ACCESS_LOG=true

# Security
GF_SECURITY_ADMIN_PASSWORD=change-me-in-production
```

Load with:

```bash
docker compose -f docker-compose.traefik.yml --env-file .env up -d
```

### SSL/TLS Certificates

**Automatic (Let's Encrypt):**
- Traefik automatically provisions certs for `api.wfc.example.com`
- Stored in `traefik-letsencrypt` volume
- Auto-renewal every 60 days

**Manual (Custom Certs):**

```yaml
# Add to traefik service in docker-compose.traefik.yml
volumes:
  - ./certs:/certs:ro
command:
  - "--providers.file.filename=/certs/traefik-tls.yml"
```

Create `certs/traefik-tls.yml`:

```yaml
tls:
  certificates:
    - certFile: /certs/cert.pem
      keyFile: /certs/key.pem
```

### Rate Limiting

Traefik rate limiting is applied **in addition to** WFC's TokenBucket (10 req/sec per project).

**Adjust Traefik limits:**

```yaml
# Line 84-85 in docker-compose.traefik.yml
- "traefik.http.middlewares.wfc-ratelimit.ratelimit.average=100"  # req/s per IP
- "traefik.http.middlewares.wfc-ratelimit.ratelimit.burst=50"     # burst size
```

### Scaling

**Horizontal scaling:**

```bash
# Scale to 5 instances
docker compose -f docker-compose.traefik.yml up -d --scale wfc-rest-api=5

# Scale down to 1
docker compose -f docker-compose.traefik.yml up -d --scale wfc-rest-api=1
```

Traefik automatically discovers new instances and load balances across all healthy backends.

## Observability

### Traefik Dashboard

Access at `http://localhost:8080/dashboard/`

Shows:
- Active routers, services, middlewares
- Backend health status
- Request rates and errors
- TLS certificate status

### Prometheus Metrics

Access at `http://localhost:9090`

**Traefik metrics:**
- `traefik_entrypoint_requests_total` - Total requests per entrypoint
- `traefik_service_requests_total` - Requests per service
- `traefik_service_request_duration_seconds` - Latency histogram

**Custom queries:**

```promql
# Request rate (last 5m)
rate(traefik_service_requests_total{service="wfc-api@docker"}[5m])

# P95 latency
histogram_quantile(0.95, traefik_service_request_duration_seconds_bucket{service="wfc-api@docker"})

# Error rate
rate(traefik_service_requests_total{service="wfc-api@docker",code=~"5.."}[5m])
```

### Grafana Dashboards

Access at `http://localhost:3000` (default: admin/admin)

**Import Traefik dashboard:**
1. Go to Dashboards → Import
2. Use dashboard ID: `17346` (Official Traefik dashboard)
3. Select Prometheus data source

### Access Logs

```bash
# Tail access logs
docker compose -f docker-compose.traefik.yml exec traefik tail -f /var/log/traefik/access.log

# Export logs
docker cp wfc-traefik:/var/log/traefik/access.log ./access.log
```

**Log format:**
```
IP - - [timestamp] "METHOD /path HTTP/1.1" status size "referer" "user-agent" latency
```

## Security

### HTTPS Enforcement

All HTTP traffic (port 80) is automatically redirected to HTTPS (port 443).

### Security Headers

Applied via middleware (lines 91-97):
- `X-Robots-Tag: noindex,nofollow` - Prevent search indexing
- `Strict-Transport-Security` - Force HTTPS for 1 year
- SSL redirect enabled

### Authentication

WFC API authentication is **unchanged** (API key via `Authorization: Bearer <key>`).

Traefik handles:
- TLS termination
- Rate limiting (IP-based)
- Access logging

### Network Isolation

Services communicate via `wfc-network` (bridge network). Only Traefik is exposed to the internet.

## Deployment Strategies

### Zero-Downtime Deploys

Current config uses `start-first` strategy:

```yaml
deploy:
  update_config:
    order: start-first  # Start new before stopping old
    parallelism: 1      # Update 1 at a time
    delay: 10s          # Wait 10s between updates
```

**Deploy process:**
1. Pull new image: `docker compose -f docker-compose.traefik.yml pull`
2. Update: `docker compose -f docker-compose.traefik.yml up -d`
3. Traefik health checks ensure traffic only goes to healthy instances

### Blue-Green Deployment

Run two full stacks and switch DNS:

```bash
# Deploy green stack
docker compose -f docker-compose.traefik.yml -p wfc-green up -d

# Test green
curl http://localhost:9950/

# Switch DNS: api.wfc.example.com → green IP

# Decommission blue
docker compose -f docker-compose.traefik.yml -p wfc-blue down
```

### Canary Deployment

Use Traefik weighted round-robin:

```yaml
# 90% to stable, 10% to canary
- "traefik.http.services.wfc-api.loadbalancer.sticky.cookie=true"
- "traefik.http.services.wfc-api-canary.loadbalancer.server.port=8001"
- "traefik.http.routers.wfc-api-secure.service=wfc-api@90,wfc-api-canary@10"
```

## Troubleshooting

### Certificate Issues

**Problem:** Let's Encrypt rate limit hit

**Solution:** Use staging endpoint during testing:

```yaml
# Add to traefik command
- "--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
```

**Problem:** Certificate not issued

**Solution:** Check DNS points to server, port 80 accessible:

```bash
# Check DNS
dig api.wfc.example.com

# Check port 80 open
curl http://api.wfc.example.com/.well-known/acme-challenge/test
```

### Load Balancing Issues

**Problem:** Requests not balanced evenly

**Solution:** Enable sticky sessions (for stateful apps):

```yaml
- "traefik.http.services.wfc-api.loadbalancer.sticky.cookie=true"
- "traefik.http.services.wfc-api.loadbalancer.sticky.cookie.name=wfc_session"
```

**Problem:** Unhealthy backend keeps receiving traffic

**Solution:** Check health check is working:

```bash
docker compose -f docker-compose.traefik.yml logs wfc-rest-api
```

Ensure health check endpoint returns 200.

### Performance Issues

**Problem:** High latency

**Check:**
1. Backend health: `curl http://localhost:9950/`
2. Traefik metrics: `http://localhost:8080/dashboard/`
3. Prometheus P95 latency query

**Optimize:**
- Increase replicas: `--scale wfc-rest-api=5`
- Enable HTTP/2: `--entrypoints.websecure.http2.maxconcurrentstreams=250`
- Tune rate limits based on actual load

## Production Checklist

Before going live:

- [ ] Update domain in `docker-compose.traefik.yml` (line 68)
- [ ] Set ACME email (line 25)
- [ ] Change Grafana admin password (line 126)
- [ ] Disable Traefik dashboard insecure mode (line 31)
- [ ] Configure firewall: allow 80, 443, 9950; block 8080, 9090, 3000
- [ ] Set up log rotation for access logs
- [ ] Configure Prometheus retention (default: 15 days)
- [ ] Test Let's Encrypt cert issuance
- [ ] Verify rate limiting: `ab -n 1000 -c 50 http://localhost:9950/`
- [ ] Load test: `locust -f tests/load/locustfile.py`
- [ ] Set up monitoring alerts (Prometheus Alertmanager)
- [ ] Document rollback procedure
- [ ] Schedule backups of `wfc-data` volume

## Backup & Recovery

### Backup WFC Data

```bash
# Backup API keys and reviews
docker run --rm -v wfc-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/wfc-data-$(date +%Y%m%d).tar.gz /data
```

### Backup Let's Encrypt Certificates

```bash
# Backup ACME JSON
docker run --rm -v traefik-letsencrypt:/data -v $(pwd):/backup alpine \
  tar czf /backup/letsencrypt-$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Restore WFC data
docker run --rm -v wfc-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/wfc-data-20260221.tar.gz -C /

# Restore certs
docker run --rm -v traefik-letsencrypt:/data -v $(pwd):/backup alpine \
  tar xzf /backup/letsencrypt-20260221.tar.gz -C /
```

## Next Steps

1. **Add monitoring alerts**: Set up Prometheus Alertmanager for SLO violations
2. **Implement API key rotation**: Add `POST /v1/projects/{id}/rotate-key` endpoint
3. **Add persistent task queue**: Replace BackgroundTasks with Celery/RQ
4. **Configure log aggregation**: Send logs to ELK/Loki
5. **Set up distributed tracing**: Add OpenTelemetry integration

## Support

- **Traefik docs**: https://doc.traefik.io/traefik/
- **WFC REST API docs**: [docs/REST_API.md](REST_API.md)
- **Issues**: https://github.com/sam-fakhreddine/wfc/issues
