# 04 — Guidelines de Arquitetura MVC

Define a estrutura **alvo** da refatoracao (Fase 3). A skill deve reestruturar o
projeto para este padrao, preservando todos os endpoints e contratos originais.

## Princípios

1. **Single Responsibility**: cada modulo/classe tem uma unica razao para mudar.
2. **Separation of Concerns**: transporte (HTTP), regras (negocio) e dados
   (persistencia) vivem em camadas distintas.
3. **Dependency Direction**: camadas externas dependem das internas, nunca o
   contrario. `routes → controllers → services → models`. Models nao importam
   routes/controllers.
4. **Composition Root**: um unico entry point (`app.py` / `app.js`) monta o app e
   injeta dependencias.
5. **Thin Controllers**: controllers orchestr chamadas a services e formatam
   respostas; nao contem regras de negocio.
6. **Preserve Contracts**: as rotas, verbos e formatos de resposta originais DEVEM
   continuar funcionando apos a refatoracao.

## Estrutura de diretorios alvo

### Python (Flask)

```
project-root/
├── config/
│   └── settings.py            # Config carregada de env (SECRET_KEY, DATABASE_URL, DEBUG)
├── models/
│   ├── __init__.py            # db = SQLAlchemy() ou factory
│   ├── produto_model.py       # So dados + serializacao (to_dict) — sem regras
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py  # Orchestr: valida input, chama service, formata resposta
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── services/                  # Quando aplicavel
│   ├── __init__.py
│   ├── pedido_service.py      # Regras de negocio (desconto, checkout, notificacao)
│   └── notificacao_service.py
├── routes/                    # "Views" no padrao MVC
│   ├── __init__.py            # registra Blueprints no app
│   ├── produto_routes.py      # @bp.route thin — so chama controller
│   └── auth_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py       # @app.errorhandler(404/500/Exception) central
│   └── auth.py                # @login_required / JWT verify
├── app.py                     # create_app() factory + registro de blueprints
├── requirements.txt
└── .env.example               # SECRET_KEY=, DATABASE_URL= (sem valores reais)
```

### Node.js (Express)

```
project-root/
├── src/
│   ├── config/
│   │   └── index.js           # carrega dotenv, exporta config
│   ├── models/
│   │   ├── userModel.js       # schema / forma dos dados
│   │   └── courseModel.js
│   ├── controllers/
│   │   ├── userController.js
│   │   └── checkoutController.js
│   ├── services/
│   │   ├── paymentService.js  # regras de pagamento
│   │   └── reportService.js
│   ├── routes/
│   │   ├── index.js           # monta todos os routers no app
│   │   ├── userRoutes.js      # router.post('/', userController.create)
│   │   └── adminRoutes.js
│   ├── middlewares/
│   │   ├── errorHandler.js    # (err, req, res, next) central
│   │   └── auth.js            # verifyToken
│   └── app.js                 # cria app Express, registra middlewares/routes
├── package.json
└── .env.example
```

## Responsabilidades por camada

### Models

- Definem a **estrutura dos dados** (campos, tipos, validacoes de schema).
- Expõem **serializacao** (`to_dict()` / `toJSON()`) — SEM campos sensiveis
  (nunca incluir `password`, `senha`, secrets).
- Podem conter **validacao de formato** (ex: `is_overdue()`, `is_admin()`).
- **NAO** contem: regras de negocio complexas, chamadas HTTP, dispatch de
  notificacao, logica de desconto/pagamento.
- **NAO** importam controllers/routes.

### Routes / Views

- Camada **HTTP fina**: registram verbos e paths, fazem parse do request, chamam
  o controller apropriado e retornam a resposta.
- **NAO** acessam DB diretamente.
- **NAO** contem regras de negocio ou validacao complexa (so delegam).
- Em Flask: usam Blueprints (`bp = Blueprint('produtos', __name__)`).
- Em Express: usam `express.Router()`.

### Controllers

- **Orquestram** o fluxo: recebem dados da rota, validam (ou delegam para schema),
  chamam services/models, formatam e retornam a resposta HTTP.
- Tratam erros de dominio (converter excecoes de service em status HTTP adequados).
- **NAO** contem regras de negocio pesadas (desconto, pagamento, notificacao) —
  essas vivem em services.

### Services (opcional mas recomendado)

- Concentram **regras de negocio** puras (sem dependencia de HTTP).
- Exemplos: `calcular_desconto(pedido)`, `processar_pagamento(cartao, valor)`,
  `notificar(usuario, evento)`.
- Podem orquestrar multiplos models/repositorios.
- Facilmente testaveis isoladamente (sem client HTTP).

### Middlewares

- **Error handler central**: captura excecoes nao tratadas e retorna JSON
  padronizado (sem vazar stack trace em producao).
- **Auth**: verifica token/sessao antes de rotas protegidas.

### Config

- Carrega **todas** as configuracoes sensiveis de variaveis de ambiente.
- Nunca contem valores hardcoded de secret.
- Expõe um objeto `Config` / `config` consumido pelo app factory.

### Entry point (`app.py` / `app.js`)

- **Composition root**: cria a instancia do app, registra middlewares, blueprints/
  routers e error handlers.
- Em Flask, preferir **factory function** `create_app()` em vez de `app = Flask(__name__)`
  no nivel do modulo (evita side-effects no import).
- Em Express, exportar uma funcao `createApp()` que monta o app.
- Nao roda o servidor quando importado (usar `if __name__ == '__main__':`).

## Checklist de aderencia MVC (Fase 3)

- [ ] `config/` existe e carrega secrets de env (sem hardcoded)
- [ ] `models/` contem so dados + serializacao (sem regras de negocio)
- [ ] `routes/`/`views/` sao finas (nao acessam DB)
- [ ] `controllers/` orchestr sem conter regras pesadas
- [ ] `services/` contem as regras de negocio extraidas
- [ ] `middlewares/error_handler` central registrado
- [ ] `middlewares/auth` protege rotas sensíveis
- [ ] Entry point usa factory `create_app()` / `createApp()`
- [ ] `.env.example` existe com as chaves necessarias (sem valores reais)
- [ ] Nenhum `SECRET_KEY`/senha hardcoded no codigo
- [ ] Todos os endpoints originais respondem (validado por `validate.sh`)
