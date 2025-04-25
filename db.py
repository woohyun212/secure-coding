import sqlite3
from flask import g, current_app

DATABASE = 'market.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Enable dict-like access by column name
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with current_app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bio TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                is_admin INTEGER NOT NULL DEFAULT 0,
                balance INTEGER NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                seller_id TEXT NOT NULL,
                image_url TEXT,
                trade_status TEXT NOT NULL DEFAULT 'available',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # NOTE: Changed `transaction` to `user_transaction` here to avoid reserved keyword conflict
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'completed'
            )
        """)

        # Ensure new columns exist when migrating existing DB
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN balance INTEGER NOT NULL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE report ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN image_url TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE product ADD COLUMN trade_status TEXT NOT NULL DEFAULT 'available'")
        except sqlite3.OperationalError:
            pass

        # Migrate price column to INTEGER if currently not INTEGER
        cursor.execute("PRAGMA table_info(product)")
        cols = cursor.fetchall()
        for col in cols:
            if col['name'] == 'price' and col['type'].upper() != 'INTEGER':
                # Rename old table
                cursor.execute("ALTER TABLE product RENAME TO product_old")
                # Recreate with INTEGER price
                cursor.execute("""
                    CREATE TABLE product (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        seller_id TEXT NOT NULL,
                        image_url TEXT,
                        trade_status TEXT NOT NULL DEFAULT 'available',
                        is_active INTEGER NOT NULL DEFAULT 1
                    )
                """)
                # Copy data, casting price to integer
                cursor.execute("""
                    INSERT INTO product (id, title, description, price, seller_id, image_url, trade_status, is_active)
                    SELECT id, title, description, CAST(price AS INTEGER), seller_id, image_url, trade_status, is_active
                    FROM product_old
                """)
                # Drop old table
                cursor.execute("DROP TABLE product_old")
                break

        db.commit()
