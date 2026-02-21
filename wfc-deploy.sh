#!/usr/bin/env bash
set -euo pipefail

# WFC Multi-Environment Deployment Manager
# Manages dev, test, and prod deployments with Traefik

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ${NC} $*"; }
log_success() { echo -e "${GREEN}✓${NC} $*"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*"; }

usage() {
    cat <<EOF
WFC Multi-Environment Deployment Manager

Usage: $0 <environment> <action> [options]

Environments:
  dev       Development (port 9950, hot reload, debug logs)
  test      Test (port 9951, 2 replicas, test data seeding)
  prod      Production (HTTPS, 3+ replicas, full observability)

Actions:
  up        Start environment
  down      Stop environment
  restart   Restart environment
  logs      View logs
  status    Show status
  scale     Scale replicas (prod/test only)
  clean     Clean volumes and data

Examples:
  $0 dev up              # Start dev environment
  $0 test up --build     # Rebuild and start test
  $0 prod up -d          # Start prod in background
  $0 prod scale 5        # Scale prod to 5 replicas
  $0 dev logs -f         # Follow dev logs
  $0 test clean          # Clean test data

Environment-specific URLs:
  Dev:  http://localhost:9950
  Test: http://localhost:9951
  Prod: https://api.wfc.example.com or http://localhost:9952

EOF
    exit 0
}

validate_env() {
    local env=$1
    case "$env" in
        dev|test|prod) return 0 ;;
        *) log_error "Invalid environment: $env"; usage ;;
    esac
}

get_compose_file() {
    local env=$1
    echo "docker-compose.$env.yml"
}

get_project_name() {
    local env=$1
    echo "wfc-$env"
}

get_env_file() {
    local env=$1
    local env_file=".env.$env"
    if [[ -f "$env_file" ]]; then
        echo "$env_file"
    else
        echo ""
    fi
}

action_up() {
    local env=$1
    shift
    local compose_file=$(get_compose_file "$env")
    local project_name=$(get_project_name "$env")
    local env_file=$(get_env_file "$env")

    log_info "Starting $env environment..."

    if [[ -n "$env_file" ]]; then
        log_info "Loading environment from $env_file"
        docker compose -f "$compose_file" -p "$project_name" --env-file "$env_file" up "$@"
    else
        docker compose -f "$compose_file" -p "$project_name" up "$@"
    fi

    if [[ $? -eq 0 ]]; then
        log_success "$env environment started"
        action_status "$env"
    fi
}

action_down() {
    local env=$1
    shift
    local compose_file=$(get_compose_file "$env")
    local project_name=$(get_project_name "$env")

    log_info "Stopping $env environment..."
    docker compose -f "$compose_file" -p "$project_name" down "$@"
    log_success "$env environment stopped"
}

action_restart() {
    local env=$1
    action_down "$env"
    action_up "$env" -d
}

action_logs() {
    local env=$1
    shift
    local compose_file=$(get_compose_file "$env")
    local project_name=$(get_project_name "$env")

    docker compose -f "$compose_file" -p "$project_name" logs "$@"
}

action_status() {
    local env=$1
    local compose_file=$(get_compose_file "$env")
    local project_name=$(get_project_name "$env")

    log_info "$env environment status:"
    docker compose -f "$compose_file" -p "$project_name" ps

    echo ""
    case "$env" in
        dev)
            log_info "Access points:"
            echo "  API:       http://localhost:9950"
            echo "  Docs:      http://localhost:9950/docs"
            echo "  Dashboard: http://localhost:8080/dashboard/"
            ;;
        test)
            log_info "Access points:"
            echo "  API:       http://localhost:9951"
            echo "  Docs:      http://localhost:9951/docs"
            echo "  Dashboard: http://localhost:8081/dashboard/"
            ;;
        prod)
            log_info "Access points:"
            echo "  API (HTTPS): https://api.wfc.example.com"
            echo "  API (Direct): http://localhost:9952"
            echo "  Grafana:     https://grafana.wfc.example.com"
            echo "  Prometheus:  https://prometheus.wfc.example.com"
            ;;
    esac
}

action_scale() {
    local env=$1
    local replicas=${2:-3}
    local compose_file=$(get_compose_file "$env")
    local project_name=$(get_project_name "$env")

    if [[ "$env" == "dev" ]]; then
        log_warning "Scaling not recommended for dev environment"
        return 1
    fi

    log_info "Scaling $env to $replicas replicas..."
    docker compose -f "$compose_file" -p "$project_name" up -d --scale wfc-rest-api="$replicas"
    log_success "Scaled to $replicas replicas"
    action_status "$env"
}

action_clean() {
    local env=$1
    local project_name=$(get_project_name "$env")

    log_warning "This will delete all data for $env environment!"
    read -p "Are you sure? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log_info "Cancelled"
        return 0
    fi

    log_info "Cleaning $env environment..."
    action_down "$env" -v

    # Remove volumes
    docker volume rm "${project_name}_wfc-${env}-data" 2>/dev/null || true
    docker volume rm "${project_name}_traefik-${env}-letsencrypt" 2>/dev/null || true
    docker volume rm "${project_name}_traefik-${env}-logs" 2>/dev/null || true

    log_success "$env environment cleaned"
}

# Main
if [[ $# -lt 2 ]]; then
    usage
fi

ENV=$1
ACTION=$2
shift 2

validate_env "$ENV"

case "$ACTION" in
    up)      action_up "$ENV" "$@" ;;
    down)    action_down "$ENV" "$@" ;;
    restart) action_restart "$ENV" ;;
    logs)    action_logs "$ENV" "$@" ;;
    status)  action_status "$ENV" ;;
    scale)   action_scale "$ENV" "$@" ;;
    clean)   action_clean "$ENV" ;;
    *)       log_error "Unknown action: $ACTION"; usage ;;
esac
