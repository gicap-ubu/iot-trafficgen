#!/usr/bin/env bash
set -euo pipefail

DB_USER="${DB_USER:-admin_iot}"
DB_PASSWORD="${DB_PASSWORD:-secreto}"
DB_NAME="${DB_NAME:-iot_db}"

echo "[infrastructure] Checking services..."

# Check Apache
if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet apache2; then
        echo "[infrastructure] Apache2: running"
    else
        echo "[infrastructure] Apache2: not running"
        echo "[infrastructure] Start with: sudo systemctl start apache2"
    fi
else
    echo "[infrastructure] systemctl not found, skipping Apache check"
fi

# Check MariaDB
if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet mariadb || systemctl is-active --quiet mysql; then
        echo "[infrastructure] MariaDB/MySQL: running"
    else
        echo "[infrastructure] MariaDB/MySQL: not running"
        echo "[infrastructure] Start with: sudo systemctl start mariadb"
    fi
else
    echo "[infrastructure] systemctl not found, skipping MariaDB check"
fi

# Check database connection
if command -v mysql &>/dev/null; then
    echo "[infrastructure] Testing database connection..."
    
    if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -e "SELECT 1;" &>/dev/null; then
        echo "[infrastructure] Database connection: OK"
        
        # Check if database exists
        if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -e "USE ${DB_NAME};" &>/dev/null; then
            echo "[infrastructure] Database '${DB_NAME}': exists"
            
            # Check if sensores table exists
            if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -e "DESCRIBE sensores;" &>/dev/null; then
                echo "[infrastructure] Table 'sensores': exists"
                
                # Count records
                COUNT=$(mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -N -e "SELECT COUNT(*) FROM sensores;")
                echo "[infrastructure] Records in 'sensores': ${COUNT}"
            else
                echo "[infrastructure] Table 'sensores': not found"
                echo "[infrastructure] Create with schema in docs/database_schema.sql"
            fi
        else
            echo "[infrastructure] Database '${DB_NAME}': not found"
            echo "[infrastructure] Create with: mysql -u root -p -e 'CREATE DATABASE ${DB_NAME};'"
        fi
    else
        echo "[infrastructure] Database connection: FAILED"
        echo "[infrastructure] Check credentials: DB_USER=${DB_USER}"
    fi
else
    echo "[infrastructure] mysql client not found"
fi

# Check PHP endpoint
if command -v curl &>/dev/null; then
    echo "[infrastructure] Testing web endpoint..."
    
    if curl -s http://localhost/index.php?id=1&batt=50 | grep -q "OK"; then
        echo "[infrastructure] Web endpoint: OK"
    else
        echo "[infrastructure] Web endpoint: not responding or not configured"
        echo "[infrastructure] Check /var/www/html/index.php"
    fi
else
    echo "[infrastructure] curl not found, skipping web endpoint test"
fi

echo "[infrastructure] Infrastructure check completed"