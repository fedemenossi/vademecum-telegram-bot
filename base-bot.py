import sqlite3

conn = sqlite3.connect("usuarios.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    nombre TEXT,
    apellido TEXT,
    consultas INTEGER DEFAULT 0,
    suscripcion_valida_hasta TEXT
)
''')

conn.commit()
conn.close()
