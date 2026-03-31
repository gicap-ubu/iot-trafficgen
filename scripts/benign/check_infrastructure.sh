#!/usr/bin/env bash
set -euo pipefail

DB_USER="${DB_USER:-admin_iot}"
DB_PASSWORD="${DB_PASSWORD:-secreto}"
DB_NAME="${DB_NAME:-iot_db}"
MQTT_HOST="${MQTT_HOST:-localhost}"
MQTT_PORT="${MQTT_PORT:-1883}"

FAILED=0

mark_failed() {
    FAILED=1
}

echo "[infrastructure] Checking services..."

# Check Apache
if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet apache2; then
        echo "[infrastructure] Apache2: running"
    else
        echo "[infrastructure] Apache2: not running"
        echo "[infrastructure] Start with: sudo systemctl start apache2"
        mark_failed
    fi
else
    echo "[infrastructure] systemctl not found, skipping Apache service-state check"
fi

# Check MariaDB / MySQL service
if command -v systemctl &>/dev/null; then
    if systemctl is-active --quiet mariadb || systemctl is-active --quiet mysql; then
        echo "[infrastructure] MariaDB/MySQL: running"
    else
        echo "[infrastructure] MariaDB/MySQL: not running"
        echo "[infrastructure] Start with: sudo systemctl start mariadb"
        mark_failed
    fi
else
    echo "[infrastructure] systemctl not found, skipping MariaDB service-state check"
fi

# Check database connection and schema
if command -v mysql &>/dev/null; then
    echo "[infrastructure] Testing database connection..."

    if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -e "SELECT 1;" &>/dev/null; then
        echo "[infrastructure] Database connection: OK"

        if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -e "USE ${DB_NAME};" &>/dev/null; then
            echo "[infrastructure] Database '${DB_NAME}': exists"

            if mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -e "DESCRIBE sensores;" &>/dev/null; then
                echo "[infrastructure] Table 'sensores': exists"

                COUNT=$(mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -N -e "SELECT COUNT(*) FROM sensores;")
                echo "[infrastructure] Records in 'sensores': ${COUNT}"
            else
                echo "[infrastructure] Table 'sensores': not found"
                echo "[infrastructure] Create the table using the SQL shown in docs/Installation.md"
                mark_failed
            fi
        else
            echo "[infrastructure] Database '${DB_NAME}': not found"
            echo "[infrastructure] Create with: mysql -u root -p -e 'CREATE DATABASE ${DB_NAME};'"
            mark_failed
        fi
    else
        echo "[infrastructure] Database connection: FAILED"
        echo "[infrastructure] Check credentials: DB_USER=${DB_USER}"
        mark_failed
    fi
else
    echo "[infrastructure] mysql client not found"
    mark_failed
fi

# Check MQTT broker
if command -v mosquitto_pub &>/dev/null; then
    echo "[infrastructure] Testing MQTT broker..."

    if mosquitto_pub -h "${MQTT_HOST}" -p "${MQTT_PORT}" -t "iottrafficgen/healthcheck" -m "ping" >/dev/null 2>&1; then
        echo "[infrastructure] MQTT broker: OK (${MQTT_HOST}:${MQTT_PORT})"
    else
        echo "[infrastructure] MQTT broker: FAILED (${MQTT_HOST}:${MQTT_PORT})"
        echo "[infrastructure] Check Mosquitto service and client connectivity"
        mark_failed
    fi
else
    echo "[infrastructure] mosquitto_pub not found"
    echo "[infrastructure] Install with: sudo apt install mosquitto-clients"
    mark_failed
fi

# Check PHP endpoint
if command -v curl &>/dev/null; then
    echo "[infrastructure] Testing web endpoint..."

    WEB_URL="http://localhost/index.php?id=1&batt=50"

    if curl -fsS --max-time 3 "${WEB_URL}" >/dev/null; then
        echo "[infrastructure] Web endpoint: OK (${WEB_URL})"
    else
        echo "[infrastructure] Web endpoint: FAILED (${WEB_URL})"
        echo "[infrastructure] Check Apache/PHP and /var/www/html/index.php"
        mark_failed
    fi
else
    echo "[infrastructure] curl not found, skipping web endpoint test"
    mark_failed
fi

if [[ "${FAILED}" -ne 0 ]]; then
    echo "[infrastructure] One or more checks failed"
    exit 1
fi

echo "[infrastructure] All checks passed"
exit 0
