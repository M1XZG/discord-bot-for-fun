# ... (previous imports)
from threading import Thread
from flask import Flask

# ... (existing code)

# --- Health check web server for Docker ---
app = Flask(__name__)

@app.route("/")
def health():
    return "Bot is running!", 200

def run_web():
    app.run(host="0.0.0.0", port=31999)

if __name__ == "__main__":
    # Start health server in a background thread
    Thread(target=run_web, daemon=True).start()
    bot.run(DISCORD_TOKEN)