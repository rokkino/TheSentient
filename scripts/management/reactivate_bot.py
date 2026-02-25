import sqlite3
conn = sqlite3.connect('backend/thesentient.db')
cursor = conn.cursor()
cursor.execute("UPDATE bots SET is_active = 1, status = 'active' WHERE id = 1")
conn.commit()
print('Bot reactivated')
conn.close()
