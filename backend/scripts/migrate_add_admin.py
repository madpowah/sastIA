import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sastIA.db")

if not os.path.exists(db_path):
    print("Database not found, skipping migration.")
    exit(0)

admin_email = os.environ.get("ADMIN_EMAIL", "")
if not admin_email:
    print("ADMIN_EMAIL environment variable not set. Skipping admin assignment.")
    print("Set ADMIN_EMAIL and re-run to grant admin privileges.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if "is_admin" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    print("Added is_admin column to users table.")
else:
    print("is_admin column already exists.")

# Set admin user from environment variable
cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (admin_email,))
if cursor.rowcount:
    print(f"Set admin flag for {admin_email}")
else:
    print(f"{admin_email} not found in database. You may need to register first, then re-run.")

conn.commit()
conn.close()
print("Migration complete.")
