#!/bin/bash

# RTF Diff App - Health Check and Monitoring Script

APP_URL="${APP_URL:-http://localhost:8000}"
LOG_FILE="/var/log/rtf-diff-health.log"
EMAIL="${ALERT_EMAIL:-admin@example.com}"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Health check function
check_health() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL" --max-time 10)
    
    if [ "$response" = "200" ]; then
        log "✅ Health check passed (HTTP $response)"
        return 0
    else
        log "❌ Health check failed (HTTP $response)"
        return 1
    fi
}

# Disk usage check
check_disk_usage() {
    local usage=$(df /tmp | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 80 ]; then
        log "⚠️  High disk usage: ${usage}%"
        # Clean up old temp files
        find /tmp -name "rtf_session_*" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null
        log "🧹 Cleaned up old temporary files"
    fi
}

# Memory usage check
check_memory() {
    local mem_usage=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')
    
    if [ "$mem_usage" -gt 90 ]; then
        log "⚠️  High memory usage: ${mem_usage}%"
    fi
}

# Main monitoring routine
main() {
    log "🔍 Starting health check..."
    
    if ! check_health; then
        log "🚨 Application is down! Attempting restart..."
        
        # Restart application (adjust for your deployment method)
        if systemctl is-active --quiet rtf-diff; then
            systemctl restart rtf-diff
            log "🔄 Restarted systemd service"
        elif docker ps | grep -q rtf-diff-app; then
            docker-compose restart rtf-diff-app
            log "🔄 Restarted Docker container"
        fi
        
        # Send alert email (if mail is configured)
        if command -v mail >/dev/null 2>&1; then
            echo "RTF Diff App is down and has been restarted. Please check logs." | \
                mail -s "RTF Diff App Alert" "$EMAIL"
        fi
    fi
    
    check_disk_usage
    check_memory
    
    log "✅ Monitoring check completed"
}

# Run the monitoring
main "$@"
