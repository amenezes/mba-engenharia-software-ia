# 04 — Guidelines de Arquitetura MVC

Define a estrutura **alvo** da refatoração (Fase 3). A skill deve reestruturar o
projeto para este padrão, preservando todos os endpoints e contratos originais.

## Princípios

1. **Single Responsibility**: cada módulo/classe tem uma única razao para mudar.
2. **Separation of Concerns**: transporte (HTTP), regras (negocio) e dados
   (persistência) vivem em camadas distintas.
3. **Dependency Direction**: camadas externas dependem das internas, nunca o
   contrário. `routes → controllers → services → models`. Models não importam
   routes/controllers.
4. **Composition Root**: um único entry point (`app.py` / `app.js`) monta o app e
   injeta dependências.
5. **Thin Controllers**: controllers orchestr chamadas a services e formatam
   respostas; não contem regras de negocio.
6. **Preserve Contracts**: as rotas, verbos e formatos de resposta originais DEVEM
   continuar funcionando após a refatoração.

## Estrutura de diretórios alvo

### Python (Flask)

```
project-root/
├── config/
│   └── settings.py            # Config carregada de env (SECRET_KEY, DATABASE_URL, DEBUG)
├── models/
│   ├── __init__.py            # db = SQLAlchemy() ou factory
│   ├── produto_model.py       # Só dados + serialização (to_dict) — sem regras
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py  # Orchestr: válida input, chama service, formata resposta
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── services/                  # Quando aplicável
│   ├── __init__.py
│   ├── pedido_service.py      # Regras de negocio (desconto, checkout, notificação)
│   └── notificacao_service.py
├── routes/                    # "Views" no padrão MVC
│   ├── __init__.py            # registra Blueprints no app
│   ├── produto_routes.py      # @bp.route thin — só chama controller
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
- Expõem **serialização** (`to_dict()` / `toJSON()`) — SEM campos sensíveis
  (nunca incluir `password`, `senha`, secrets).
- Podem conter **validação de formato** (ex: `is_overdue()`, `is_admin()`).
- **NÃO** contem: regras de negocio complexas, chamadas HTTP, dispatch de
  notificação, lógica de desconto/pagamento.
- **NÃO** importam controllers/routes.

### Routes / Views

- Camada **HTTP fina**: registram verbos e paths, fazem parse do request, chamam
  o controller apropriado e retornam a resposta.
- **NÃO** acessam DB diretamente.
- **NÃO** contem regras de negocio ou validação complexa (só delegam).
- Em Flask: usam Blueprints (`bp = Blueprint('produtos', __name__)`).
- Em Express: usam `express.Router()`.

### Controllers

- **Orquestram** o fluxo: recebem dados da rota, validam (ou delegam para schema),
  chamam services/models, formatam e retornam a resposta HTTP.
- Tratam erros de domínio (converter exceções de service em status HTTP adequados).
- **NÃO** contem regras de negocio pesadas (desconto, pagamento, notificação) —
  essas vivem em services.

### Services (opcional mas recomendado)

- Concentram **regras de negocio** puras (sem dependência de HTTP).
- Exemplos: `calcular_desconto(pedido)`, `processar_pagamento(cartao, valor)`,
  `notificar(usuario, evento)`.
- Podem orquestrar multiplos models/repositorios.
- Facilmente testaveis isoladamente (sem client HTTP).

### Middlewares

- **Error handler central**: captura exceções não tratadas e retorna JSON
  padronizado (sem vazar stack trace em producao).
- **Auth**: verifica token/sessão antes de rotas protegidas.

### Config

- Carrega **todas** as configuracoes sensíveis de variáveis de ambiente.
- Nunca contem valores hardcoded de secret.
- Expõe um objeto `Config` / `config` consumido pelo app factory.

### Entry point (`app.py` / `app.js`)

- **Composition root**: cria a instancia do app, registra middlewares, blueprints/
  routers e error handlers.
- Em Flask, preferir **factory function** `create_app()` em vez de `app = Flask(__name__)`
  no nivel do módulo (evita side-effects no import).
- Em Express, exportar uma função `createApp()` que monta o app.
- Não roda o servidor quando importado (usar `if __name__ == '__main__':`).

## Checklist de aderencia MVC (Fase 3)

- [ ] `config/` existe e carrega secrets de env (sem hardcoded)
- [ ] `models/` contem só dados + serialização (sem regras de negocio)
- [ ] `routes/`/`views/` são finas (não acessam DB)
- [ ] `controllers/` orchestr sem conter regras pesadas
- [ ] `services/` contem as regras de negocio extraidas
- [ ] `middlewares/error_handler` central registrado
- [ ] `middlewares/auth` protege rotas sensíveis
- [ ] Entry point usa factory `create_app()` / `createApp()`
- [ ] `.env.example` existe com as chaves necessarias (sem valores reais)
- [ ] Nenhum `SECRET_KEY`/senha hardcoded no código
- [ ] Todos os endpoints originais respondem (validado por `validate.sh`)
