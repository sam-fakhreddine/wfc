# WFC Multi-Environment Deployment

Run dev, test, and prod environments simultaneously with complete isolation.

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Your Machine                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ DEV (9950)   │  │ TEST (9951)  │  │ PROD (9952)  │ │
│  │              │  │              │  │              │ │
│  │ 1 instance   │  │ 2 instances  │  │ 3 instances  │ │
│  │ Hot reload   │  │ Test data    │  │ HTTPS        │ │
│  │ Debug logs   │  │ Load balance │  │ Observability│ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Environment Files

```bash
# Copy example configs
cp .env.dev.example .env.dev
cp .env.test.example .env.test
cp .env.prod.example .env.prod

# Edit production config
vim .env.prod  # Set PROD_DOMAIN, ACME_EMAIL, passwords
```

### 2. Start Environments

```bash
# Start dev (port 9950)
./wfc-deploy.sh dev up -d

# Start test (port 9951)
./wfc-deploy.sh test up -d

# Start prod (HTTPS + port 9952)
./wfc-deploy.sh prod up -d
```

### 3. Verify

```bash
# Check all environments
./wfc-deploy.sh dev status
./wfc-deploy.sh test status
./wfc-deploy.sh prod status

# Test each API
curl http://localhost:9950/     # Dev
curl http://localhost:9951/     # Test
curl http://localhost:9952/     # Prod (direct)
curl https://api.wfc.example.com/  # Prod (HTTPS)
```

## Environment Comparison

| Feature | Dev | Test | Prod |
|---------|-----|------|------|
| **Port** | 9950 | 9951 | 443, 9952 |
| **Instances** | 1 | 2 | 3+ |
| **HTTPS** | No | No | Yes (Let's Encrypt) |
| **Hot Reload** | Yes | No | No |
| **Log Level** | DEBUG | INFO | WARN |
| **Traefik Dashboard** | :8080 | :8081 | Secured |
| **Data Seeding** | Manual | Auto | No |
| **Observability** | No | Metrics only | Full stack |
| **Resource Limits** | No | No | Yes |
| **Sticky Sessions** | No | No | Yes |
| **Compression** | No | No | Yes |
| **Rate Limiting** | No | Yes | Yes (200 req/s) |

## Environment Details

### Development (Port 9950)

**Purpose:** Local development with instant feedback

**Features:**
- Single instance (no load balancing)
- Hot reload on code changes
- Debug logging enabled
- Traefik dashboard at `:8080`
- No HTTPS (localhost only)

**Start:**
```bash
./wfc-deploy.sh dev up
```

**Usage:**
```bash
# API
curl http://localhost:9950/v1/projects/

# Interactive docs
open http://localhost:9950/docs

# Dashboard
open http://localhost:8080/dashboard/
```

**Code Changes:**
- Mounted volumes: `./wfc:/app/wfc:rw`
- Changes take effect immediately (uvicorn --reload)

### Test (Port 9951)

**Purpose:** Integration testing and load testing

**Features:**
- 2 instances with load balancing
- Auto-seeded test data
- Health checks enabled
- Traefik dashboard at `:8081`
- Prometheus metrics

**Start:**
```bash
./wfc-deploy.sh test up -d

# Wait for test data seeding
docker logs wfc-test-seeder
```

**Usage:**
```bash
# API (load balanced)
curl http://localhost:9951/v1/projects/

# Test with pre-created projects
# Project 1: test-project-1 (alice)
# Project 2: test-project-2 (bob)
```

**Load Testing:**
```bash
# Using ab (ApacheBench)
ab -n 1000 -c 50 http://localhost:9951/

# Using locust
locust -f tests/load/locustfile.py --host http://localhost:9951
```

### Production (HTTPS + Port 9952)

**Purpose:** Production deployment with full security and observability

**Features:**
- 3+ instances with auto-scaling
- HTTPS with Let's Encrypt
- Full observability (Prometheus, Grafana, Alertmanager)
- Security headers, rate limiting, compression
- Resource limits and health checks
- Zero-downtime deploys

**Start:**
```bash
# First time: configure .env.prod
vim .env.prod

# Start
./wfc-deploy.sh prod up -d
```

**Usage:**
```bash
# HTTPS (primary)
curl https://api.wfc.example.com/v1/projects/

# Direct access (optional, can be disabled)
curl http://localhost:9952/v1/projects/

# Monitoring
open https://grafana.wfc.example.com       # Grafana
open https://prometheus.wfc.example.com    # Prometheus
open https://traefik.wfc.example.com       # Traefik (basic auth)
```

## Management Commands

### Start/Stop

```bash
# Start environment
./wfc-deploy.sh <env> up          # Foreground
./wfc-deploy.sh <env> up -d       # Background
./wfc-deploy.sh <env> up --build  # Rebuild images

# Stop environment
./wfc-deploy.sh <env> down        # Stop and remove containers
./wfc-deploy.sh <env> down -v     # Also remove volumes

# Restart
./wfc-deploy.sh <env> restart
```

### Logs

```bash
# View all logs
./wfc-deploy.sh <env> logs

# Follow logs
./wfc-deploy.sh <env> logs -f

# Specific service
./wfc-deploy.sh <env> logs wfc-rest-api

# Last 100 lines
./wfc-deploy.sh <env> logs --tail=100
```

### Status

```bash
# Check status and URLs
./wfc-deploy.sh <env> status

# Docker ps output
./wfc-deploy.sh <env> status | grep wfc-rest-api
```

### Scaling

```bash
# Scale test to 5 instances
./wfc-deploy.sh test scale 5

# Scale prod to 10 instances
./wfc-deploy.sh prod scale 10

# Scale down to 1
./wfc-deploy.sh test scale 1
```

### Clean

```bash
# Remove all data for environment
./wfc-deploy.sh <env> clean

# Requires confirmation (type "yes")
```

## Running Multiple Environments

```bash
# Start all three simultaneously
./wfc-deploy.sh dev up -d
./wfc-deploy.sh test up -d
./wfc-deploy.sh prod up -d

# Check status of all
for env in dev test prod; do
    echo "=== $env ==="
    ./wfc-deploy.sh $env status
    echo ""
done

# Stop all
for env in dev test prod; do
    ./wfc-deploy.sh $env down
done
```

## Port Reference

| Environment | API | Dashboard | Prometheus | Grafana |
|-------------|-----|-----------|------------|---------|
| Dev | 9950 | 8080 | - | - |
| Test | 9951 | 8081 | - | - |
| Prod | 9952, 443 | HTTPS only | 9090 | 3000 |

## Data Isolation

Each environment has isolated data:

```
~/.wfc/                    # Shared config
docker volumes:
  wfc-dev-data             # Dev data
  wfc-test-data            # Test data
  wfc-prod-data            # Prod data
  traefik-dev-logs         # Dev Traefik logs
  traefik-test-logs        # Test Traefik logs
  traefik-prod-logs        # Prod Traefik logs
  traefik-prod-letsencrypt # Prod SSL certs
```

## Network Isolation

Each environment runs in its own Docker network:

- `wfc-dev-network`
- `wfc-test-network`
- `wfc-prod-network`

No cross-environment communication possible.

## Typical Workflow

### 1. Develop Locally (Dev)

```bash
# Start dev
./wfc-deploy.sh dev up

# Make code changes in wfc/
# Changes apply immediately (hot reload)

# Test locally
curl http://localhost:9950/v1/projects/
```

### 2. Integration Test (Test)

```bash
# Start test environment
./wfc-deploy.sh test up -d

# Run integration tests
pytest tests/integration/ --host http://localhost:9951

# Load test
ab -n 10000 -c 100 http://localhost:9951/

# Check metrics
open http://localhost:8081/dashboard/
```

### 3. Deploy to Production (Prod)

```bash
# Build production image
./wfc-deploy.sh prod up -d --build

# Verify health
curl https://api.wfc.example.com/

# Monitor
open https://grafana.wfc.example.com

# Watch logs
./wfc-deploy.sh prod logs -f wfc-rest-api
```

## Environment-Specific Configuration

### Dev Configuration

```yaml
# docker-compose.dev.yml
services:
  wfc-rest-api:
    volumes:
      - ./wfc:/app/wfc:rw  # Read-write for hot reload
    environment:
      - RELOAD=true        # Uvicorn --reload
      - LOG_LEVEL=debug
```

### Test Configuration

```yaml
# docker-compose.test.yml
services:
  wfc-rest-api:
    deploy:
      replicas: 2          # Test load balancing
  test-seeder:             # Auto-seed test data
    command: seed_test_projects.sh
```

### Prod Configuration

```yaml
# docker-compose.prod.yml
services:
  wfc-rest-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
      update_config:
        order: start-first  # Zero-downtime
```

## Troubleshooting

### Port Conflicts

**Problem:** Port already in use

**Solution:** Check what's using the port:

```bash
lsof -i :9950  # Dev
lsof -i :9951  # Test
lsof -i :9952  # Prod

# Kill the process or change port in docker-compose.<env>.yml
```

### Environment Confusion

**Problem:** Not sure which environment is running

**Solution:** Check all:

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep wfc
```

### SSL Certificate Issues (Prod)

**Problem:** Let's Encrypt rate limit

**Solution:** Use staging during setup:

```bash
# Edit .env.prod
ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory

# Restart
./wfc-deploy.sh prod restart
```

### Data Corruption

**Problem:** Environment data is corrupted

**Solution:** Clean and restart:

```bash
./wfc-deploy.sh <env> clean
./wfc-deploy.sh <env> up -d
```

## Best Practices

1. **Always use environment-specific ports** - Don't change the default ports
2. **Test in 'test' before 'prod'** - Always validate in test environment first
3. **Monitor prod continuously** - Use Grafana dashboards
4. **Back up prod data** - Regular backups of `wfc-prod-data` volume
5. **Use .env files** - Don't hardcode credentials in compose files
6. **Keep dev clean** - Regularly `./wfc-deploy.sh dev clean`
7. **Scale gradually** - Don't jump from 3 to 100 instances
8. **Watch resource usage** - Monitor CPU/memory in prod

## Next Steps

- Set up CI/CD pipeline (deploy to test, then prod)
- Configure Prometheus alerts
- Add custom Grafana dashboards
- Implement blue-green deployment
- Set up log aggregation (ELK/Loki)
