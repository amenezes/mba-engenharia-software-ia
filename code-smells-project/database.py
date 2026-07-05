import sqlite3

from werkzeug.security import generate_password_hash

from config.settings import Config

db_connection = None


def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(
            Config.DATABASE_PATH, check_same_thread=False
        )
        db_connection.row_factory = sqlite3.Row
        init_db(db_connection)
    return db_connection


def init_db(db):
    cursor = db.cursor()
    cursor.executescript(_SCHEMA_SQL)
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        _seed(db)
    db.commit()


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco REAL,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    status TEXT DEFAULT 'pendente',
    total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    preco_unitario REAL
);
"""


def _seed(db):
    cursor = db.cursor()
    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonomico", 89.90, 50, "informatica"),
        ("Teclado Mecanico", "Teclado mecanico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonomica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa codigo", 59.90, 100, "vestuario"),
    ]
    cursor.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        produtos,
    )
    usuarios_seed = [
        ("Admin", "admin@loja.com", generate_password_hash(Config.SEED_ADMIN_PASSWORD), "admin"),
        ("Joao Silva", "joao@email.com", generate_password_hash(Config.SEED_CLIENT_PASSWORD), "cliente"),
        ("Maria Santos", "maria@email.com", generate_password_hash(Config.SEED_CLIENT2_PASSWORD), "cliente"),
    ]
    cursor.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios_seed,
    )
