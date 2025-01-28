import nextcord
from nextcord.ext import commands
import logging
import os
import json
from dotenv import load_dotenv  # Import dotenv to load environment variables
import re
from datetime import datetime, timedelta
from flask import Flask, render_template
import threading  # Import threading to run Flask in a separate thread
import asyncio

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load the Discord token from the environment variable
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Check if the token is loaded correctly
if DISCORD_TOKEN is None:
    logging.error('DISCORD_TOKEN is not set. Please check your .env file.')
    exit(1)

# Define intents
intents = nextcord.Intents.default()
intents.messages = True
intents.message_content = False  # Disable message content intent
intents.members = False  # Disable member intents

# Initialize the bot
APPLICATION_ID = '1285549408087310408'
bot = commands.Bot(command_prefix='/', intents=intents, application_id=APPLICATION_ID)

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Render the index.html file

@app.route('/index')
def index():
    return render_template('index.html')  # Additional route for index if needed

def run_flask():
    port = int(os.environ.get('PORT', 5000))  # Use PORT environment variable
    app.run(host='0.0.0.0', port=port)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')

@bot.command()
async def ping(ctx):
    logging.info("Ping command received")  # Debug print
    try:
        await ctx.send('Pong!')
    except Exception as e:
        logging.error(f'Error sending ping response: {e}')

# Define regex patterns
patterns = [
    r'^.*([A-Za-z0-9]+( [A-Za-z0-9]+)+).*[A-Za-z]+.*$',
    r'^<#(\d{17,20})>$',
    r'(\w+)?\.?dis(?:cord)?(?:app|merch|status)?\.(com|g(?:d|g|ift)|(?:de(?:sign|v))|media|new|store|net)',
    r'[a4]?+[b8]+c+d+[e3]?+f+g9]+h+[i1l]?+j+k+[l1i]+(m|nn|rn)+n+[o0]?+p+q+r+[s5]+[t7]+[uv]?+v+(w|vv|uu)+x+y+z+0+9+8+7+6+5+4+3+2+1+',
    r'^https?:\/\/',
    r'^<@&(\d{17,20})>$',
    r'^<@!?(\\d{17,20})>$',
    r'^wss?:\/\/',
    r'https:\/\/(?:(?:canary|ptb).)?discord(?:app)?.com\/api(?:\/v\d+)?\/webhooks\/(\d+)\/([\w-]+)\/?$',
    r'[^\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]',
    r'<@!?\d{17,20}>'  # Added regex for user mentions
]

@bot.slash_command(name='ping', description='Responds with Pong!')
async def ping_slash(interaction: nextcord.Interaction):
    await interaction.response.send_message('Pong!')

@bot.slash_command(name='botinfo', description='Get information about the bot')
async def botinfo_slash(interaction: nextcord.Interaction):
    bot_info = {
        'name': bot.user.name,  # Use 'name' instead of 'username'
        'id': bot.user.id,
        'created_at': str(bot.user.created_at),
        'guilds': [guild.name for guild in bot.guilds],
        'prefix': bot.command_prefix,
        'description': bot.description,
        'owner_id': bot.owner_id,
        'owner': bot.owner,
        'latency': bot.latency
    }
    await interaction.response.send_message(f'```json\n{json.dumps(bot_info, indent=2)}\n```')

@bot.slash_command(name='serversettings', description='Get information about the server')
async def serversettings_slash(interaction: nextcord.Interaction):
    guild = interaction.guild
    server_settings = {
        'name': guild.name,
        'id': guild.id,
        'member_count': guild.member_count,
        'roles': [role.name for role in guild.roles],
        'channels': [channel.name for channel in guild.channels],
        'owner_id': guild.owner_id,
        'owner': guild.owner,
        'created_at': str(guild.created_at),
        'icon_url': str(guild.icon_url)
    }
    await interaction.response.send_message(f'```json\n{json.dumps(server_settings, indent=2)}\n```')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    logging.info(f"Received message: {message.content}")  # Debug print

    # Check if the message matches any of the regex patterns
    for pattern in patterns:
        if re.match(pattern, message.content):
            logging.info(f"Deleted message: {message.content} matching pattern: {pattern}")  # Debug print
            try:
                await message.delete()  # Delete the message
            except Exception as e:
                logging.error(f'Error deleting message: {e}')
            break  # Exit the loop after deleting

    # Check if the bot has permission to timeout the user
    if message.author.top_role >= message.guild.me.top_role:
        await message.channel.send("I cannot timeout this user because my role is lower.")
        return

    # Set the duration for the timeout (e.g., 3 minutes)
    timeout_duration = timedelta(minutes=3)
    timeout_until = datetime.utcnow() + timeout_duration  # Use utcnow() for an aware datetime

    try:
        await message.author.timeout(timeout_until, reason="Automatic timeout for every message")
        await message.channel.send(f'{message.author.mention} has been timed out for 3 minutes.')
    except Exception as e:
        logging.error(f'Error timing out {message.author}: {e}')

    await bot.process_commands(message)  # Ensure commands are processed

async def main():
    logging.info("Starting bot...")  # Debug print
    try:
        # Start Flask server in a separate thread
        threading.Thread(target=run_flask).start()
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logging.error(f'Error starting bot: {e}')

if __name__ == "__main__":
    asyncio.run(main())
