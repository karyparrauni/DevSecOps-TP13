#!/bin/bash
# verificar-zap.sh
# Valida la sintaxis del plan localmente si tenés Docker
echo "=== Verificando Plan de ZAP AF ==="
docker run --rm -v $(pwd):/zap/wrk/:rw -t zaproxy/zap-stable zap.sh \
    -cmd -autorun /zap/wrk/.zap/zap-plan.yml

