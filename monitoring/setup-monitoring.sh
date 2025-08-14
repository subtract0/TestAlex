#!/bin/bash
# ACIM Guide Monitoring Stack Setup Script
# Deploys Prometheus, Alertmanager, Grafana, and Chaos Engineering system
# 
# "In quietness are all things answered, and is every problem quietly resolved." - ACIM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="acim-guide-monitoring"
ENVIRONMENT=${ENVIRONMENT:-production}

echo -e "${BLUE}🙏 ACIM Guide Monitoring Stack Setup${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed. Please install it first.${NC}"
        exit 1
    fi
}

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        echo -e "${YELLOW}📁 Creating directory: $1${NC}"
        mkdir -p "$1"
    fi
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
check_command "docker"
check_command "docker-compose"
check_command "openssl"

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
create_dir "${SCRIPT_DIR}/logs"
create_dir "${SCRIPT_DIR}/chaos-logs"
create_dir "${SCRIPT_DIR}/chaos-reports"
create_dir "${SCRIPT_DIR}/grafana/dashboards"
create_dir "${SCRIPT_DIR}/grafana/provisioning/dashboards"
create_dir "${SCRIPT_DIR}/grafana/provisioning/datasources"
create_dir "${SCRIPT_DIR}/alertmanager-templates"
create_dir "${SCRIPT_DIR}/nginx/ssl"

# Generate environment file if it doesn't exist
ENV_FILE="${SCRIPT_DIR}/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚙️ Generating .env file...${NC}"
    cat > "$ENV_FILE" << EOF
# ACIM Guide Monitoring Stack Environment Variables
COMPOSE_PROJECT_NAME=${PROJECT_NAME}
ENVIRONMENT=${ENVIRONMENT}

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$(generate_password)

# Grafana Cloud Integration (optional)
GRAFANA_CLOUD_PROMETHEUS_URL=https://prometheus-prod-01-eu-west-0.grafana.net/api/prom/push
GRAFANA_CLOUD_PROMETHEUS_USER=your-user
GRAFANA_CLOUD_API_KEY=your-api-key
GRAFANA_CLOUD_PUSH_URL=https://prometheus-prod-01-eu-west-0.grafana.net/api/prom/push
GRAFANA_CLOUD_USER=your-user  
GRAFANA_CLOUD_PASSWORD=your-password

# PagerDuty Integration
PAGERDUTY_INTEGRATION_KEY=your-pagerduty-integration-key

# Slack Integration  
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_API_URL=https://slack.com/api/chat.postMessage

# Email Configuration
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=alerts@acim-guide.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=alerts@acim-guide.com

# Firebase Configuration
FIREBASE_PROJECT_ID=acim-guide-test

# Security
SECRET_KEY=$(generate_password)
EOF
    echo -e "${GREEN}✅ Created .env file with generated passwords${NC}"
    echo -e "${YELLOW}⚠️  Please update the .env file with your actual API keys and credentials${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Check for Firebase service account key
FIREBASE_KEY="${SCRIPT_DIR}/acim-guide-test-firebase-adminsdk.json"
if [ ! -f "$FIREBASE_KEY" ]; then
    echo -e "${YELLOW}⚠️  Firebase service account key not found${NC}"
    echo -e "${YELLOW}   Please download the service account key from Firebase Console${NC}"
    echo -e "${YELLOW}   and save it as: ${FIREBASE_KEY}${NC}"
    echo -e "${YELLOW}   The monitoring stack will still start, but Firebase metrics will be simulated${NC}"
fi

# Create Grafana provisioning files
echo -e "${BLUE}📊 Setting up Grafana provisioning...${NC}"

cat > "${SCRIPT_DIR}/grafana/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
  - name: Alertmanager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: true
EOF

cat > "${SCRIPT_DIR}/grafana/provisioning/dashboards/dashboard.yml" << EOF
apiVersion: 1

providers:
  - name: 'ACIM Guide Dashboards'
    orgId: 1
    folder: 'ACIM Guide'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Create basic Alertmanager templates
echo -e "${BLUE}📧 Setting up Alertmanager templates...${NC}"

cat > "${SCRIPT_DIR}/alertmanager-templates/email.tmpl" << 'EOF'
{{ define "email.default" }}
<!DOCTYPE html>
<html>
<head>
    <title>ACIM Guide Alert</title>
</head>
<body>
    <h2>🚨 ACIM Guide System Alert</h2>
    
    {{ range .Alerts }}
    <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
        <h3 style="color: {{ if eq .Status "firing" }}red{{ else }}green{{ end }};">
            {{ .Annotations.summary }}
        </h3>
        <p><strong>Description:</strong> {{ .Annotations.description }}</p>
        <p><strong>Severity:</strong> {{ .Labels.severity }}</p>
        <p><strong>Instance:</strong> {{ .Labels.instance }}</p>
        <p><strong>Started:</strong> {{ .StartsAt }}</p>
        
        {{ if .Annotations.suggested_actions }}
        <h4>Suggested Actions:</h4>
        <p>{{ .Annotations.suggested_actions }}</p>
        {{ end }}
        
        {{ if .Annotations.runbook_url }}
        <p><a href="{{ .Annotations.runbook_url }}">📖 View Runbook</a></p>
        {{ end }}
    </div>
    {{ end }}
    
    <hr>
    <p><em>"The truth needs no defense; it merely is." - ACIM</em></p>
    <p>Dashboard: <a href="https://monitoring.acim-guide.com">https://monitoring.acim-guide.com</a></p>
</body>
</html>
{{ end }}
EOF

# Create Nginx configuration
echo -e "${BLUE}🌐 Setting up Nginx configuration...${NC}"

cat > "${SCRIPT_DIR}/nginx/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream prometheus {
        server prometheus:9090;
    }
    
    upstream alertmanager {
        server alertmanager:9093;
    }
    
    upstream grafana {
        server grafana:3000;
    }

    server {
        listen 80;
        server_name monitoring.acim-guide.com;
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name monitoring.acim-guide.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        location / {
            proxy_pass http://grafana;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /alertmanager/ {
            proxy_pass http://alertmanager/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

# Generate self-signed certificates for development
if [ ! -f "${SCRIPT_DIR}/nginx/ssl/cert.pem" ]; then
    echo -e "${BLUE}🔒 Generating self-signed SSL certificates...${NC}"
    openssl req -x509 -newkey rsa:4096 -keyout "${SCRIPT_DIR}/nginx/ssl/key.pem" \
        -out "${SCRIPT_DIR}/nginx/ssl/cert.pem" -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=ACIM Guide/CN=monitoring.acim-guide.com"
fi

# Set proper permissions
echo -e "${BLUE}🔐 Setting permissions...${NC}"
chmod 600 "${SCRIPT_DIR}/nginx/ssl/key.pem"
chmod 644 "${SCRIPT_DIR}/nginx/ssl/cert.pem"
chmod 600 "$ENV_FILE"

# Build and start the monitoring stack
echo -e "${BLUE}🚀 Building and starting monitoring stack...${NC}"

cd "$SCRIPT_DIR"

# Load environment variables
set -a
source .env
set +a

echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker-compose build

echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🏥 Checking service health...${NC}"

check_service() {
    local service=$1
    local port=$2
    local path=${3:-/}
    
    if curl -s -f "http://localhost:${port}${path}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is healthy${NC}"
    else
        echo -e "${RED}❌ $service is not responding${NC}"
    fi
}

check_service "Firebase Exporter" 9090 "/health"
check_service "Prometheus" 9091 "/-/healthy"
check_service "Alertmanager" 9093 "/-/healthy"
check_service "Grafana" 3000 "/api/health"

# Display access information
echo -e "\n${GREEN}🎉 ACIM Guide Monitoring Stack Setup Complete!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "\n${BLUE}📊 Service Access URLs:${NC}"
echo -e "🔥 Firebase Metrics Exporter: http://localhost:9090"
echo -e "📈 Prometheus: http://localhost:9091"
echo -e "🚨 Alertmanager: http://localhost:9093"
echo -e "📊 Grafana: http://localhost:3000"
echo -e "🎭 Chaos Engineer: http://localhost:8888"

echo -e "\n${BLUE}🔐 Grafana Credentials:${NC}"
echo -e "Username: admin"
echo -e "Password: $(grep GRAFANA_ADMIN_PASSWORD .env | cut -d'=' -f2)"

echo -e "\n${BLUE}🎯 Next Steps:${NC}"
echo -e "1. Update .env file with your PagerDuty and Slack credentials"
echo -e "2. Add your Firebase service account key"
echo -e "3. Configure Grafana Cloud integration (optional)"
echo -e "4. Set up DNS for monitoring.acim-guide.com"
echo -e "5. Replace self-signed certificates with real ones for production"

echo -e "\n${BLUE}🎭 Chaos Engineering:${NC}"
echo -e "• Schedule quarterly drill: docker-compose exec chaos-engineer python3 holy-spirit-chaos-drill.py schedule"
echo -e "• Execute chaos test: docker-compose exec chaos-engineer python3 holy-spirit-chaos-drill.py execute --experiment holy_spirit_outage_q1"
echo -e "• View chaos report: docker-compose exec chaos-engineer python3 holy-spirit-chaos-drill.py report --experiment holy_spirit_outage_q1"

echo -e "\n${YELLOW}💡 Remember: 'Miracles are natural. When they do not occur something has gone wrong.' - ACIM${NC}"
echo -e "${YELLOW}   Your monitoring system is now watching over the ACIM Guide with divine precision! 🙏${NC}"
