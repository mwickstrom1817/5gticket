import psycopg2
import bcrypt

conn = psycopg2.connect("postgresql://neondb_owner:npg_gN5cRzuFOPl8@ep-cold-heart-a4kyy545-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
cur = conn.cursor()

password = "$5GSecurity2026!"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

cur.execute("""
    INSERT INTO users (name, email, password, role)
    VALUES (%s, %s, %s, 'admin')
""", ("Matthew Wickstrom", "mwickstrom@fivegsecurity.com", hashed))

conn.commit()
cur.close()
conn.close()
print("Admin created.")