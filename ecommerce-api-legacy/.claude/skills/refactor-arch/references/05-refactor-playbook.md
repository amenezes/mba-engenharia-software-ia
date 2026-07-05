# 05 — Playbook de Refatoracao

**12 transformacoes concretas** com exemplo antes/depois em **Python e Node.js**.
Cada transformacao referencia o anti-pattern correspondente no
[catálogo](02-antipatterns-catalog.md).

**Principio de agnosticidade**: Cada transformacao descreve primeiro o **padrao
abstrato** (o que fazer e por que) e depois exemplos concretos em Python e Node.js
(como fazer em cada ecossistema). Para outras stacks, aplique o padrao usando a
biblioteca padrao ou idioma canonico do ecossistema detectado na Fase 1.
Ex: "substituir hash quebrado por algoritmo de derivacao de chave com salt"
aplica-se a qualquer linguagem; a escolha da biblioteca (werkzeug, bcrypt, argon2,
crypto.scrypt) depende do ecossistema.

Principios:
- Aplique as transformacoes na ordem de severidade dos findings (CRITICAL primeiro).
- Preserve os contratos HTTP (rotas, verbos, formatos de resposta).
- Quando um anti-pattern aparecer varias vezes, aplique a transformacao em todos os
  locais (nao so no primeiro).

---

## 1. Extrair secrets para env

**Anti-pattern**: #1 Hardcoded Secrets

**Python — antes** (`app.py`):
```python
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha-chave-super-secreta-123'
```

**Python — depois** (`config/settings.py`):
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-change-me'
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///loja.db')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
```

`app.py`:
```python
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    ...
    return app
```

`.env.example`:
```
SECRET_KEY=
DATABASE_URL=sqlite:///loja.db
FLASK_DEBUG=0
```

**Node — antes** (`utils.js`):
```js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000,
};
```

**Node — depois** (`src/config/index.js`):
```js
require('dotenv').config();

const config = {
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: process.env.PORT || 3000,
};

module.exports = config;
```

`.env.example`:
```
DB_PASS=
PAYMENT_GATEWAY_KEY=
PORT=3000
```

---

## 2. Hash de senha seguro

**Anti-pattern**: #2 Insecure Password Storage

**Python — antes** (`models/user.py`):
```python
import hashlib
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Python — depois**:
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

(Adicionar `werkzeug` ja vem com Flask; `bcrypt` opcional via `methods=['bcrypt']`.)

**Node — antes** (`utils.js`):
```js
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

**Node — depois** (`src/services/passwordService.js`):
```js
const bcrypt = require('bcrypt');

async function hashPassword(pwd) {
    return bcrypt.hash(pwd, 12);
}

async function verifyPassword(pwd, hash) {
    return bcrypt.compare(pwd, hash);
}

module.exports = { hashPassword, verifyPassword };
```

(Adicionar `bcrypt` ao `package.json`.)

---

## 3. Remover campos sensíveis da serializacao

**Anti-pattern**: #3 Sensitive Data Exposure

**Python — antes** (`models/user.py`):
```python
def to_dict(self):
    return {
        'id': self.id,
        'email': self.email,
        'password': self.password,   # VAZANDO
    }
```

**Python — depois**:
```python
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        # password intencionalmente omitido
    }
```

**Node — antes** (`AppManager.js`):
```js
app.get('/api/users', (req, res) => {
    db.all("SELECT * FROM users", [], (err, users) => {
        res.json(users);   // retorna 'pass' junto
    });
});
```

**Node — depois** (`src/controllers/userController.js`):
```js
function toSafeUser(u) {
    const { pass, password, ...safe } = u;
    return safe;
}

exports.list = (req, res) => {
    userModel.findAll((err, users) => {
        if (err) return next(err);
        res.json(users.map(toSafeUser));
    });
};
```

Tambem: **parar de logar PAN/secrets**. Remover `console.log(\`Processando cartão ${cc}...\`)`.

---

## 4. Parametrizar queries

**Anti-pattern**: #4 SQL Injection

**Python — antes** (`models.py`):
```python
def get_usuario_por_id(id):
    cursor.execute("SELECT * FROM usuarios WHERE id = " + str(id))
def login(email, senha):
    cursor.execute(f"SELECT * FROM usuarios WHERE email = '{email}' AND senha = '{senha}'")
```

**Python — depois**:
```python
def get_usuario_por_id(id):
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
def login(email, senha_hash):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND password = ?",
        (email, senha_hash)
    )
```

**Node — antes**:
```js
db.run(`INSERT INTO users (name) VALUES ('${req.body.name}')`);
```

**Node — depois**:
```js
db.run("INSERT INTO users (name) VALUES (?)", [req.body.name], function(err) { ... });
```

> Atencao: queries com `?`/`[params]` ja estavam corretas no `ecommerce-api-legacy`
> — nesse projeto, a transformacao e principalmente mover o SQL para um
> repository/model (ver #6) e nao a parametrizacao em si.

---

## 5. Desligar debug + factory `create_app`

**Anti-pattern**: #6 Debug Mode RCE

**Python — antes** (`app.py`):
```python
app = Flask(__name__)
app.config['DEBUG'] = True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**Python — depois** (`app.py`):
```python
from config.settings import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    register_blueprints(app)
    register_error_handlers(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=app.config['DEBUG'])
```

(bind em `127.0.0.1` por default; DEBUG via env, default False.)

**Node — antes** (`app.js`):
```js
const express = require('express');
const app = express();
app.listen(config.port, () => console.log('running'));
// sem error handler, sem graceful shutdown
```

**Node — depois** (`src/app.js`):
```js
const express = require('express');
const { errorHandler } = require('./middlewares/errorHandler');

function createApp() {
    const app = express();
    app.use(express.json({ limit: '1mb' }));
    app.use(require('./routes'));
    app.use(errorHandler);   // centralizado, por ultimo
    return app;
}

const app = createApp();
const server = app.listen(config.port, () => console.log(`running on ${config.port}`));
process.on('SIGTERM', () => server.close(() => process.exit(0)));

module.exports = { createApp };
```

---

## 6. Decompor God Class

**Anti-pattern**: #5 God Class / God Method

Transforma um arquivo/classe que concentra DB + rotas + regras em camadas MVC.

**Python — antes** (`models.py` 314 LOC com produtos+usuarios+pedidos+itens juntos):

**Depois**: separar por dominio em arquivos pequenos:
```
models/produto_model.py     (produto: queries + to_dict)
models/usuario_model.py     (usuario: queries + hash + to_dict)
models/pedido_model.py      (pedido + itens: queries + to_dict)
controllers/pedido_controller.py  (orchestr + validacao)
services/pedido_service.py        (regras: checkout, desconto)
routes/pedido_routes.py           (Blueprint thin)
```

**Node — antes** (`AppManager.js` — classe com DB + schema + setupRoutes + regras):

**Depois**:
```
src/models/userModel.js          (acesso a tabela users)
src/models/courseModel.js        (acesso a courses)
src/models/enrollmentModel.js    (acesso a enrollments + payments)
src/controllers/checkoutController.js
src/controllers/adminController.js
src/services/paymentService.js   (regras de pagamento)
src/services/reportService.js    (agregacoes do relatorio)
src/routes/index.js              (monta todos os routers)
src/db.js                        (conexao + schema bootstrap isolados)
```

Remover a classe `AppManager`; o `createApp()` em `src/app.js` monta tudo.

---

## 7. Adicionar camada de autenticação

**Anti-pattern**: #7 Missing AuthN/AuthZ

**Python — depois** (`middlewares/auth.py`):
```python
from functools import wraps
from flask import request, jsonify
import jwt

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token ausente'}), 401
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            request.current_user_id = payload['sub']
        except jwt.PyJWTError:
            return jsonify({'error': 'Token invalido'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # adicional: checar role == 'admin'
        ...
    return decorated
```

Uso:
```python
@admin_bp.route('/reset-db', methods=['POST'])
@admin_required
def reset_database():
    ...
```

E `/login` deve emitir um **JWT real** (não `fake-jwt-token-<id>`):
```python
def login(email, senha):
    user = usuario_model.autenticar(email, senha)
    if not user:
        return None
    token = jwt.encode(
        {'sub': user['id'], 'role': user['role'], 'exp': datetime.utcnow() + timedelta(hours=8)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token
```

**Node — depois** (`src/middlewares/auth.js`):
```js
const jwt = require('jsonwebtoken');

function verifyToken(req, res, next) {
    const auth = req.headers.authorization;
    if (!auth || !auth.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Token ausente' });
    }
    try {
        req.user = jwt.verify(auth.slice(7), process.env.JWT_SECRET);
        next();
    } catch (e) {
        return res.status(401).json({ error: 'Token invalido' });
    }
}

function requireAdmin(req, res, next) {
    if (req.user?.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
    next();
}

module.exports = { verifyToken, requireAdmin };
```

Uso:
```js
adminRouter.get('/financial-report', verifyToken, requireAdmin, adminController.report);
```

(Adicionar `PyJWT` / `jsonwebtoken` às deps.)

---

## 8. Mover lógica de negócio para Services

**Anti-pattern**: #8 Business Logic in Routes/Controllers

**Python — antes** (`controllers.py`):
```python
def criar_pedido(dados):
    # validacao + regra de desconto + notificacao tudo aqui dentro
    total = sum(...)
    if total > 10000:
        total *= 0.9
    print("ENVIANDO EMAIL/SMS/PUSH")
    ...
```

**Depois** (`services/pedido_service.py`):
```python
DESCONTO_ALTO = 10000
TAXA_DESCONTO_ALTO = 0.10

def calcular_total_com_desconto(itens):
    total = sum(i['preco'] * i['quantidade'] for i in itens)
    if total >= DESCONTO_ALTO:
        total *= (1 - TAXA_DESCONTO_ALTO)
    return total

def processar_checkout(usuario_id, itens):
    total = calcular_total_com_desconto(itens)
    pedido = pedido_model.criar(usuario_id, itens, total)
    notificacao_service.notificar_novo_pedido(pedido)
    return pedido
```

`controllers/pedido_controller.py` fica fino:
```python
def criar():
    dados = request.get_json()
    pedido = pedido_service.processar_checkout(dados['usuario_id'], dados['itens'])
    return jsonify(pedido.to_dict()), 201
```

**Node — antes** (`AppManager.js` com pagamento + enrollment + audit inline):
**Depois** (`src/services/checkoutService.js` + `paymentService.js`):
```js
async function checkout({ userId, courseId, card }) {
    const payment = await paymentService.charge({ card, amount: course.price });
    if (payment.status !== 'PAID') throw new PaymentError('recusado');
    const enrollment = await enrollmentModel.create({ userId, courseId });
    await auditModel.log({ action: 'checkout', enrollmentId: enrollment.id });
    return { enrollment, payment };
}
```

---

## 9. Resolver N+1 com JOIN / joinedload / GROUP BY

**Anti-pattern**: #9 N+1 / Queries in Loops

**Python — antes** (`models.py`):
```python
def get_todos_pedidos():
    pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
    for p in pedidos:
        itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(p['id'])).fetchall()
        for it in itens:
            prod = cursor.execute("SELECT * FROM produtos WHERE id = " + str(it['produto_id'])).fetchone()
```

**Python — depois** (1 query com JOIN):
```python
def get_todos_pedidos():
    return cursor.execute("""
        SELECT p.*, ip.quantidade, ip.preco_unitario, pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        ORDER BY p.id
    """).fetchall()
```

Se usando SQLAlchemy: `Pedido.query.options(joinedload(Pedido.itens).joinedload(Item.produto)).all()`.

Para agregacoes (COUNT): substituir loop Python por `GROUP BY`:
```python
# antes: for u in users: count = Task.query.filter_by(user_id=u.id).count()
# depois:
stats = db.session.query(User.id, func.count(Task.id))\
    .outerjoin(Task, Task.user_id == User.id)\
    .group_by(User.id).all()
```

**Node — antes** (`AppManager.js` N+1 quadrático):
**Depois** (1 query com JOIN):
```js
const sql = `
    SELECT c.title, u.name AS student, p.status, p.amount
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
`;
db.all(sql, [], (err, rows) => { /* agrupa em JS */ });
```

---

## 10. Centralizar error handling

**Anti-pattern**: #11 No Centralized Error Handling

**Python — depois** (`middlewares/error_handler.py`):
```python
from flask import Flask, jsonify
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Recurso nao encontrado'}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Requisicao invalida'}), 400

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro nao tratado")
        return jsonify({'error': 'Erro interno'}), 500
```

Remover os `return str(e)` e `except: pass` espalhados — deixar excecoes
propagarem ate o handler central.

**Node — depois** (`src/middlewares/errorHandler.js`):
```js
const winston = require('winston');
const logger = winston.createLogger({ /* ... */ });

function errorHandler(err, req, res, next) {
    logger.error(err.message, { stack: err.stack, path: req.path });
    const status = err.status || 500;
    res.status(status).json({
        error: status === 500 ? 'Erro interno' : err.message,
    });
}

// custom errors
class PaymentError extends Error { constructor(m){ super(m); this.status=400; } }

module.exports = { errorHandler, PaymentError };
```

Registrar **depois** das rotas em `createApp()`. Remover `catch (err) {}` vazios.

---

## 11. Migrar APIs deprecated

**Anti-pattern**: #10 Deprecated API Usage

**Python (SQLAlchemy 2.x) — antes**:
```python
user = User.query.get(user_id)          # legacy
users = User.query.all()
```

**Depois**:
```python
user = db.session.get(User, user_id)    # SQLAlchemy 2.x
users = db.session.execute(db.select(User)).scalars().all()
```

**Node — antes**:
```js
const sqlite3 = require('sqlite3').verbose();   // verbose() ruidoso
app.use(require('body-parser').json());          // deprecated
db.run(sql, function(err) { ... });              // callback hell
```

**Depois**:
```js
const sqlite3 = require('sqlite3');              // sem verbose()
app.use(express.json({ limit: '1mb' }));         // nativo do Express 4.16+
// wrap em Promise:
const db = new sqlite3.Database(':memory:');
function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            if (err) reject(err); else resolve(this);
        });
    });
}
```

---

## 12. Extrair constantes/enums + eliminar duplicação

**Anti-pattern**: #12 Magic Numbers/Strings + DRY

**Python — depois** (`models/constants.py` ou `config/constants.py`):
```python
from enum import Enum

class PaymentStatus(Enum):
    PAID = 'PAID'
    DENIED = 'DENIED'
    PENDING = 'PENDING'

class TaskStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    CANCELLED = 'cancelled'

VALID_STATUSES = [s.value for s in TaskStatus]
PRIORITY_MIN = 1
PRIORITY_MAX = 5

# descontos
LIMITE_DESCONTO_ALTO = 10000
TAXA_DESCONTO_ALTO = 0.10
LIMITE_DESCONTO_MEDIO = 5000
TAXA_DESCONTO_MEDIO = 0.05
```

**Eliminar duplicação** — funções quase idênticas viram uma com parametro:
```python
# antes: get_pedidos_usuario(id) e get_todos_pedidos() com 90% do corpo igual
# depois:
def get_pedidos(usuario_id=None):
    sql = """
        SELECT p.*, ip.quantidade, pr.nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
    """
    params = ()
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params = (usuario_id,)
    return cursor.execute(sql, params).fetchall()
```

**Node — depois** (`src/config/constants.js`):
```js
const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
    PENDING: 'PENDING',
});
module.exports = { PAYMENT_STATUS };
```

Usar `PAYMENT_STATUS.PAID` em vez do literal `"PAID"` espalhado.

---

## Ordem de aplicação sugerida

1. #1 Secrets → #5 Debug/factory → #2 Hash → #3 Sensitive fields (segurança base)
2. #4 SQL param → #9 N+1 (integridade/performance de dados)
3. #6 Decompor God Class → #8 Services (estrutura MVC)
4. #7 Auth → #10 Error handler (cross-cutting)
5. #11 Deprecated → #12 Constants/DRY (limpeza)
