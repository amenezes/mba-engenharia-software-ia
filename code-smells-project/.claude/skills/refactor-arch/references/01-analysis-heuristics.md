# 01 — Heuristicas de Analise de Projeto

Esta referencia orienta a **Fase 1** da skill: detectar stack, dominio e
arquitetura atual de um projeto qualquer, de forma agnostica de tecnologia.

## 1. Detectar a linguagem

Procure pelos manifestos na raiz do projeto:

| Manifesto              | Linguagem        | Como ler                          |
| ---------------------- | ---------------- | --------------------------------- |
| `requirements.txt`     | Python           | linhas `<pkg>==<versao>`          |
| `pyproject.toml`       | Python           | `[project.dependencies]`          |
| `setup.py`             | Python (legado)  | `install_requires=[...]`          |
| `package.json`         | Node.js / JS     | `"dependencies": { ... }`         |
| `go.mod`               | Go               | `require (...)`                   |
| `pom.xml` / `build.gradle` | Java         | tags `<dependency>`               |
| `Cargo.toml`           | Rust             | `[dependencies]`                  |
| `composer.json`        | PHP              | `"require": { ... }`              |

Confirme pela extensao predominante dos arquivos fonte: `.py`, `.js`/`.ts`,
`.go`, `.java`, `.rs`, `.php`.

Grep uteis para confirmar Python:
```
rg -l "import |from .* import |def |class " --type py
```

Grep uteis para confirmar Node.js:
```
rg -l "require\(|module\.exports|const |import .* from" --type js
```

## 2. Detectar o framework e versao exata

Leia o manifesto de dependencias e procure por frameworks web conhecidos:

**Python** (`requirements.txt` / `pyproject.toml`):

| Framework        | String de deteccao          |
| ---------------- | --------------------------- |
| Flask            | `flask==<X>` ou `Flask==`   |
| FastAPI          | `fastapi==`                 |
| Django           | `django==` ou `Django==`    |
| Bottle           | `bottle==`                  |
| Tornado          | `tornado==`                 |

Extraia a versao exata do `==<versao>`. Se houver `flask-cors`, `flask-sqlalchemy`,
`flask-login`, liste-os tambem.

**Node.js** (`package.json` → `dependencies`):

| Framework / lib  | String de deteccao          |
| ---------------- | --------------------------- |
| Express          | `"express": "^<X>"`         |
| Fastify          | `"fastify":`                |
| Koa              | `"koa":`                    |
| NestJS           | `"@nestjs/core":`           |

Para o Express, detecte tambem middlewares relevantes: `cors`, `helmet`,
`body-parser` (deprecated quando separado), `morgan`, `express-validator`.

**Go** (`go.mod`):

| Framework / lib  | String de deteccao             |
| ---------------- | ------------------------------ |
| Gin              | `github.com/gin-gonic/gin`     |
| Echo             | `github.com/labstack/echo`     |
| Fiber            | `github.com/gofiber/fiber`     |
| Chi              | `github.com/go-chi/chi`        |

**Java** (`pom.xml` / `build.gradle`):

| Framework / lib  | String de deteccao                    |
| ---------------- | ------------------------------------- |
| Spring Boot      | `spring-boot-starter-web`             |
| Quarkus          | `quarkus-resteasy`                    |
| Micronaut        | `micronaut-http-server`               |

**Rust** (`Cargo.toml`):

| Framework / lib  | String de deteccao       |
| ---------------- | ------------------------ |
| Actix Web        | `actix-web`              |
| Axum             | `axum`                   |
| Rocket           | `rocket`                 |

**PHP** (`composer.json`):

| Framework / lib  | String de deteccao          |
| ---------------- | --------------------------- |
| Laravel          | `laravel/framework`         |
| Symfony          | `symfony/http-kernel`       |
| Slim             | `slim/slim`                 |

## 3. Detectar o banco de dados

Procure por sinais no codigo fonte (Grep):

| Tecnologia         | Sinais (regex)                                              |
| ------------------ | ----------------------------------------------------------- |
| SQLite (raw)       | `import sqlite3` (Python) / `require\(['"]sqlite3` (Node)   |
| SQLAlchemy         | `from sqlalchemy` / `flask_sqlalchemy` / `SQLAlchemy(`      |
| Mongoose           | `require\(['"]mongoose`                                     |
| MySQL/Postgres     | `pymysql`, `psycopg`, `mysql2`, `pg`                        |
| In-memory          | `:memory:` (SQLite) / objetos JS `let .* = \[\]`            |

Identifique as **tabelas / collections** procurando por:
- Python: `CREATE TABLE`, `db.Table(`, `__tablename__`, `class .*\(db\.Model\)`
- Node: `CREATE TABLE`, `mongoose.Schema(`, `db.collection(`

Liste as tabelas encontradas.

## 4. Identificar o dominio

O dominio e inferido pelos nomes de entidades/tabelas/rotas:

- Liste as rotas HTTP registradas (Grep por `@app.route`, `@.*\.route`,
  `app\.(get|post|put|delete|patch)`, `add_url_rule`, `router\.(get|post)`).
- Liste os models/classes de dominio (`class .*\(db\.Model\)`, `class .*Model`,
  `mongoose.model(`).
- Agrupe por recurso e descreva o dominio em uma frase. Exemplos:
  - tabelas `produtos, usuarios, pedidos` → "E-commerce API (produtos, pedidos, usuarios)"
  - rotas `/api/courses`, `/api/checkout`, tabelas `enrollments, payments` → "LMS API com checkout"
  - tabelas `tasks, users, categories` → "Task Manager API"

## 5. Mapear a arquitetura atual

Avalie o **grau de separacao de responsabilidades**:

1. **Conte os arquivos fonte** (excluindo `node_modules`, `.venv`, `__pycache__`,
   `tests`, migracoes):
   ```
   rg --files --type py | wc -l      # Python
   rg --files -g "*.js" -g "!node_modules" | wc -l   # Node
   ```
2. **Conte LOC por arquivo** (`wc -l` ou `rg --count-matches ''`).
3. **Verifique a estrutura de diretorios**:
   - Ha pastas `models/`, `routes/` ou `views/`, `controllers/`, `services/`?
   - Elas estao **populadas** ou vazias?
4. **Teste se a separacao e real ou cosmetica**:
   - Os `services/` sao realmente importados? Grep por `from .*services` ou
     `require.*services`. Se ninguem importa, e MVC cosmetico.
   - Os models tem logica de negocio? (metodos com regras de desconto, pagamento,
     notificacao dentro de models.py/model.js).
   - As rotas acessam o DB diretamente? Grep por `cursor.execute`, `db.run`,
     `Model.query` dentro de arquivos de rota.
5. **Classifique a arquitetura**:
   - **Monolito flat**: poucos arquivos, tudo junto, sem pastas.
   - **God Object**: uma classe/arquivo concentra DB + rotas + regras.
   - **MVC cosmetico**: pastas existem mas services mortos, logica nas rotas.
   - **MVC parcial**: algumas camadas ok, outras violadas.
   - **MVC real**: separacao efetiva (raro nos projetos-alvo).

## 6. Exemplo de saida

Para `code-smells-project`:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuarios)
Architecture:  Monolitica — tudo em 4 arquivos, sem separacao de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```
