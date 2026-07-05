#!/usr/bin/env bash
#
# validate.sh — Smoke test pos-refatoracao (Fase 3 da skill refactor-arch).
#
# Detecta o runtime (Python/Node), sobe a aplicacao em background, faz curl nos
# endpoints mapeados, verifica os status HTTP e derruba a app.
#
# Saida: linhas "[pass]"/"[fail]" para cada cheque e exit code 0 (tudo ok) ou 1.
#
# Uso: bash ${CLAUDE_SKILL_DIR}/scripts/validate.sh
#      bash validate.sh [ENDPOINT_EXTRA1] [ENDPOINT_EXTRA2] ...

set -u

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
PASS_COUNT=0
FAIL_COUNT=0
APP_PID=""

cleanup() {
    if [ -n "$APP_PID" ] && kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

log_pass() { echo "  [pass] $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
log_fail() { echo "  [fail] $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# Endpoints padrao a testar (alimento de GET; sem auth esperado para smoke).
# Endpoints extras podem ser passados como argumentos.
DEFAULT_ENDPOINTS=( "/health" "/" )
EXTRA_ENDPOINTS=( "$@" )
ALL_ENDPOINTS=( "${DEFAULT_ENDPOINTS[@]}" "${EXTRA_ENDPOINTS[@]}" )

echo "================================"
echo "PHASE 3: VALIDATION"
echo "================================"
echo "Project: $(basename "$PROJECT_DIR")"
echo ""

# ---------------------------------------------------------------------------
# Detectar runtime e entry point
# ---------------------------------------------------------------------------
ENTRY=""
RUNTIME=""

if [ -f "app.py" ]; then
    ENTRY="app.py"; RUNTIME="python"
elif [ -f "src/app.js" ] && [ -f "package.json" ]; then
    ENTRY="src/app.js"; RUNTIME="node"
elif [ -f "app.js" ] && [ -f "package.json" ]; then
    ENTRY="app.js"; RUNTIME="node"
elif [ -f "server.js" ] && [ -f "package.json" ]; then
    ENTRY="server.js"; RUNTIME="node"
elif [ -f "main.py" ]; then
    ENTRY="main.py"; RUNTIME="python"
fi

if [ -z "$ENTRY" ]; then
    log_fail "Nenhum entry point encontrado (app.py / app.js / server.js)"
    echo ""
    echo "================================"
    echo "Result: FAIL (no entry point)"
    echo "================================"
    exit 1
fi
echo "Runtime:    $RUNTIME"
echo "Entry:      $ENTRY"

# ---------------------------------------------------------------------------
# Detectar o executavel do runtime (python3/python, node; venvs locais)
# ---------------------------------------------------------------------------
PYTHON_BIN=""
NODE_BIN=""

detect_python() {
    if [ -n "${PYTHON:-}" ] && command -v "$PYTHON" >/dev/null 2>&1; then
        PYTHON_BIN="$PYTHON"; return
    fi
    for cand in \
        "./venv/bin/python" "./.venv/bin/python" \
        "../venv/bin/python" "../.venv/bin/python" \
        "../../.venv/bin/python" \
        "python3" "python"; do
        if command -v "$cand" >/dev/null 2>&1; then
            PYTHON_BIN="$cand"; return
        elif [ -x "$cand" ]; then
            PYTHON_BIN="$cand"; return
        fi
    done
}

detect_node() {
    if [ -n "${NODE:-}" ] && command -v "$NODE" >/dev/null 2>&1; then
        NODE_BIN="$NODE"; return
    fi
    for cand in "./node_modules/.bin/node" "node" "nodejs"; do
        if command -v "$cand" >/dev/null 2>&1; then
            NODE_BIN="$cand"; return
        fi
    done
}

if [ "$RUNTIME" = "python" ]; then
    detect_python
    if [ -z "$PYTHON_BIN" ]; then
        log_fail "Executavel python nao encontrado (tentou python3, python, venvs locais)"
        echo "  Dica: ative o venv ou exporte PYTHON=/caminho/python"
    fi
elif [ "$RUNTIME" = "node" ]; then
    detect_node
    if [ -z "$NODE_BIN" ]; then
        log_fail "Executavel node nao encontrado"
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Cheque 1: imports / sintaxe (boot sem rede)
# ---------------------------------------------------------------------------
echo "[1/3] Verificando sintaxe/imports..."
if [ "$RUNTIME" = "python" ] && [ -n "$PYTHON_BIN" ]; then
    if "$PYTHON_BIN" -m py_compile "$ENTRY" 2>/dev/null; then
        log_pass "$PYTHON_BIN -m py_compile $ENTRY"
    else
        log_fail "$PYTHON_BIN -m py_compile $ENTRY"
    fi
elif [ "$RUNTIME" = "node" ] && [ -n "$NODE_BIN" ]; then
    if "$NODE_BIN" --check "$ENTRY" 2>/dev/null; then
        log_pass "$NODE_BIN --check $ENTRY"
    else
        log_fail "$NODE_BIN --check $ENTRY"
    fi
fi

# ---------------------------------------------------------------------------
# Cheque 2: subir a aplicacao
# ---------------------------------------------------------------------------
echo ""
echo "[2/3] Subindo a aplicacao..."
PORT="${VALIDATE_PORT:-0}"
# Tenta portas de 5050 a 5070 para evitar conflito
if [ "$PORT" = "0" ]; then
    for P in 5050 5051 5052 5053 5054 5055 5056 5057 5058 5059 5060; do
        if ! command -v ss >/dev/null 2>&1 || ! ss -ltn "( sport = :$P )" 2>/dev/null | grep -q ":$P"; then
            PORT="$P"; break
        fi
    done
fi
BASE_URL="http://127.0.0.1:${PORT}"
echo "  Tentando porta $PORT..."

BOOT_OK=0
if [ "$RUNTIME" = "python" ] && [ -n "$PYTHON_BIN" ]; then
    # Tenta exporter FLASK_APP primeiro; fallback roda o arquivo direto
    if [ -n "${FLASK_APP:-}" ] || "$PYTHON_BIN" -c "import flask" 2>/dev/null; then
        FLASK_APP="${FLASK_APP:-${ENTRY%.py}}" FLASK_RUN_HOST=127.0.0.1 FLASK_RUN_PORT="$PORT" \
            "$PYTHON_BIN" -m flask run --no-debugger --no-reload >/tmp/validate_app.log 2>&1 &
        APP_PID=$!
    else
        PORT_ENV="$PORT" "$PYTHON_BIN" "$ENTRY" >/tmp/validate_app.log 2>&1 &
        APP_PID=$!
    fi
elif [ "$RUNTIME" = "node" ] && [ -n "$NODE_BIN" ]; then
    PORT="$PORT" "$NODE_BIN" "$ENTRY" >/tmp/validate_app.log 2>&1 &
    APP_PID=$!
fi

# Espera o boot (ate 15s)
BOOT_OK=0
for i in $(seq 1 30); do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        echo "  Processo morreu antes do boot. Log:"
        tail -n 20 /tmp/validate_app.log 2>/dev/null
        break
    fi
    if curl -sf -o /dev/null "$BASE_URL/health" 2>/dev/null \
        || curl -sf -o /dev/null "$BASE_URL/" 2>/dev/null; then
        BOOT_OK=1; break
    fi
    sleep 0.5
done

if [ "$BOOT_OK" = "1" ]; then
    log_pass "Application boots without errors (pid $APP_PID na porta $PORT)"
else
    log_fail "Application boots without errors"
    echo "  Log de boot:"
    tail -n 30 /tmp/validate_app.log 2>/dev/null | sed 's/^/    /'
fi

# ---------------------------------------------------------------------------
# Cheque 3: endpoints respondem
# ---------------------------------------------------------------------------
echo ""
echo "[3/3] Testando endpoints..."
if [ "$BOOT_OK" = "1" ]; then
    for ep in "${ALL_ENDPOINTS[@]}"; do
        # Faz apenas GET para smoke (nao destructive)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$BASE_URL$ep" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" = "000" ]; then
            log_fail "GET $ep -> sem resposta"
        elif [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 400 ]; then
            log_pass "GET $ep -> $HTTP_CODE"
        else
            # 4xx/5xx ainda indica que o servidor respondeu; 404 = rota nao existe
            if [ "$HTTP_CODE" = "404" ]; then
                echo "  [skip] GET $ep -> 404 (rota nao existe, pulando)"
            else
                log_fail "GET $ep -> $HTTP_CODE"
            fi
        fi
    done
fi

# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------
echo ""
echo "================================"
echo "Validation summary"
echo "  Pass: $PASS_COUNT"
echo "  Fail: $FAIL_COUNT"
if [ "$FAIL_COUNT" = "0" ]; then
    echo "  Result: PASS"
    echo "================================"
    exit 0
else
    echo "  Result: FAIL"
    echo "================================"
    exit 1
fi
