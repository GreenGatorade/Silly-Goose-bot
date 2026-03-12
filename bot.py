import discord
from discord.ext import commands
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, Response, jsonify
from threading import Thread
from datetime import datetime
import csv
from io import StringIO

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Flask web app for CSV downloads
app = Flask(__name__)

# Database connection
def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        os.environ.get('DATABASE_URL'),
        cursor_factory=RealDictCursor
    )

def init_database():
    """Create messages table if it doesn't exist"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            message_id TEXT,
            user_id TEXT,
            username TEXT,
            user_tag TEXT,
            channel_id TEXT,
            channel_name TEXT,
            guild_id TEXT,
            guild_name TEXT,
            content TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Create indexes for faster queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized successfully")

# Discord event handlers
@bot.event
async def on_ready():
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📊 Logging messages from {len(bot.guilds)} server(s)')
    init_database()
    print('🌐 Web interface available on Railway URL')

@bot.event
async def on_message(message):
    # Don't log bot messages (optional - remove this line to log bot messages)
    if message.author.bot:
        return
    
    # Prepare message data
    message_data = {
        'message_id': str(message.id),
        'user_id': str(message.author.id),
        'username': message.author.name,
        'user_tag': str(message.author),
        'channel_id': str(message.channel.id),
        'channel_name': message.channel.name if hasattr(message.channel, 'name') else 'DM',
        'guild_id': str(message.guild.id) if message.guild else 'DM',
        'guild_name': message.guild.name if message.guild else 'Direct Message',
        'content': message.content,
        'timestamp': message.created_at.isoformat()
    }
    
    # Insert into database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO messages (message_id, user_id, username, user_tag, channel_id, 
                                 channel_name, guild_id, guild_name, content, timestamp)
            VALUES (%(message_id)s, %(user_id)s, %(username)s, %(user_tag)s, %(channel_id)s,
                   %(channel_name)s, %(guild_id)s, %(guild_name)s, %(content)s, %(timestamp)s)
        """, message_data)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"📝 Logged message from {message_data['username']}: {message_data['content'][:50]}...")
    except Exception as e:
        print(f"Error inserting message: {e}")
    
    # Process commands if any
    await bot.process_commands(message)

# Flask routes for web interface
@app.route('/')
def home():
    """Main dashboard page"""
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Discord Message Logger</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #5865F2;
                    margin-bottom: 10px;
                }
                .subtitle {
                    color: #666;
                    margin-top: 0;
                }
                .stats {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .button {
                    display: inline-block;
                    background-color: #5865F2;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 10px 5px;
                    font-weight: bold;
                    transition: background-color 0.2s;
                }
                .button:hover {
                    background-color: #4752C4;
                }
                .button.secondary {
                    background-color: #747F8D;
                }
                .button.secondary:hover {
                    background-color: #5C6470;
                }
                .feature-list {
                    list-style: none;
                    padding: 0;
                }
                .feature-list li {
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }
                .feature-list li:last-child {
                    border-bottom: none;
                }
                .emoji {
                    margin-right: 8px;
                }
            </style>
        </head>
        <body>
            <h1>📊 Discord Message Logger</h1>
            <p class="subtitle">Powered by PostgreSQL on Railway (Python Edition)</p>
            
            <div class="stats">
                <h2>Quick Actions</h2>
                <a href="/download/csv" class="button">⬇️ Download All Messages (CSV)</a>
                <a href="/recent" class="button secondary">👁️ View Recent Messages</a>
                <a href="/api/stats" class="button secondary">📈 View Statistics (JSON)</a>
            </div>
            
            <div class="stats">
                <h3>📋 What's Being Logged</h3>
                <ul class="feature-list">
                    <li><span class="emoji">👤</span> User information (ID, username, tag)</li>
                    <li><span class="emoji">💬</span> Message content</li>
                    <li><span class="emoji">📍</span> Channel and server details</li>
                    <li><span class="emoji">🕐</span> Precise timestamps</li>
                </ul>
            </div>
            
            <div class="stats">
                <h3>ℹ️ About</h3>
                <p>This bot logs all messages from your Discord server(s) to a persistent PostgreSQL database.</p>
                <p>Data is preserved between deployments and can be downloaded as CSV for analysis.</p>
            </div>
        </body>
        </html>
    """)

@app.route('/download/csv')
def download_csv():
    """Download all messages as CSV"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM messages ORDER BY timestamp DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Create CSV
        output = StringIO()
        if rows:
            fieldnames = ['id', 'message_id', 'user_id', 'username', 'user_tag', 
                         'channel_id', 'channel_name', 'guild_id', 'guild_name', 
                         'content', 'timestamp']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                # Convert timestamp to string if needed
                row_dict = dict(row)
                if 'timestamp' in row_dict and row_dict['timestamp']:
                    row_dict['timestamp'] = str(row_dict['timestamp'])
                if 'created_at' in row_dict:
                    del row_dict['created_at']
                writer.writerow(row_dict)
        
        # Create response
        csv_data = output.getvalue()
        output.close()
        
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=discord_messages_{int(datetime.now().timestamp())}.csv'
        
        print(f"📥 CSV downloaded with {len(rows)} messages")
        return response
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return f"Error generating CSV: {e}", 500

@app.route('/recent')
def recent_messages():
    """View recent messages in HTML table"""
    try:
        limit = int(request.args.get('limit', 100))
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        # Build table rows
        table_rows = ""
        for row in rows:
            timestamp = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if row['timestamp'] else ''
            table_rows += f"""
                <tr>
                    <td>{timestamp}</td>
                    <td>{row['username']}</td>
                    <td>{row['channel_name']}</td>
                    <td>{row['guild_name']}</td>
                    <td class="content" title="{row['content']}">{row['content']}</td>
                </tr>
            """
        
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Recent Messages</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                        max-width: 1400px; 
                        margin: 20px auto; 
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    h1 { color: #5865F2; }
                    .controls {
                        background: white;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        background: white;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    th, td { 
                        padding: 12px; 
                        text-align: left; 
                        border-bottom: 1px solid #ddd; 
                    }
                    th { 
                        background-color: #5865F2; 
                        color: white; 
                        position: sticky; 
                        top: 0;
                    }
                    tr:hover { 
                        background-color: #f5f5f5; 
                    }
                    .content { 
                        max-width: 500px; 
                        overflow: hidden; 
                        text-overflow: ellipsis; 
                        white-space: nowrap; 
                    }
                    .back { 
                        display: inline-block; 
                        color: #5865F2; 
                        text-decoration: none;
                        font-weight: bold;
                    }
                    .back:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="controls">
                    <a href="/" class="back">← Back to Dashboard</a>
                </div>
                <h1>Recent {{ count }} Messages</h1>
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>User</th>
                            <th>Channel</th>
                            <th>Server</th>
                            <th>Content</th>
                        </tr>
                    </thead>
                    <tbody>
                        {{ table_rows|safe }}
                    </tbody>
                </table>
            </body>
            </html>
        """, table_rows=table_rows, count=len(rows))
    except Exception as e:
        print(f"Error fetching recent messages: {e}")
        return f"Error retrieving messages: {e}", 500

@app.route('/api/stats')
def stats():
    """Get statistics as JSON"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT channel_id) as unique_channels,
                COUNT(DISTINCT guild_id) as unique_servers,
                MIN(timestamp) as first_message,
                MAX(timestamp) as last_message
            FROM messages
        """)
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        # Convert datetime to string
        stats_dict = dict(result)
        if stats_dict['first_message']:
            stats_dict['first_message'] = str(stats_dict['first_message'])
        if stats_dict['last_message']:
            stats_dict['last_message'] = str(stats_dict['last_message'])
        
        return jsonify({
            'stats': stats_dict,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check for Railway"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

def run_flask():
    """Run Flask app in separate thread"""
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Check for Discord token
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable is not set!")
        print("Please set it in Railway dashboard under Variables")
        exit(1)
    
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Discord bot (blocking)
    bot.run(DISCORD_TOKEN)
