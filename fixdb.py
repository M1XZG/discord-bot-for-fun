import sqlite3

DB_FILE = "fishing_game.db"

def update_fish_names():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Update all catch_name values for fish (not users) from _ to -
    c.execute("""
        UPDATE catches
        SET catch_name = REPLACE(catch_name, '_', '-')
        WHERE catch_type = 'fish' AND INSTR(catch_name, '_') > 0
    """)
    affected = c.rowcount
    conn.commit()
    conn.close()
    print(f"Updated {affected} rows in {DB_FILE} (catch_name: _ → -)")

if __name__ == "__main__":
    update_fish_names()