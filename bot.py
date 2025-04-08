import nextcord
from nextcord.ext import commands, tasks
import logging
import os
import json
from dotenv import load_dotenv  # Import dotenv to load environment variables
import re
from datetime import datetime, timedelta
from flask import Flask, render_template
import threading  # Import threading to run Flask in a separate thread
import asyncio
from nextcord import Intents
import time

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

# Initialize intents
intents = Intents.default()
intents.messages = True  # Enable message intents

# Initialize Bot
bot = commands.Bot(command_prefix='/', intents=intents)

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
    app.run(host='0.0.0.0', port=port, use_reloader=False)  # Disable reloader to prevent issues

# Define regex patterns for automod globally
patterns = [
    r'https?://\S+',  # Matches any URL
    r'\b(spam|advertisement|link|buy|free|click here|subscribe)\b',  # Matches common spam phrases
    r'discord\.gg/\S+',  # Matches Discord invite links
    r'<@!?\d{17,20}>',  # Matches user mentions
    r'(.)\1{3,}',  # Matches any character repeated 4 or more times
    r'[^\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]',  # Your first pattern
    r'^.*([A-Za-z0-9]+( [A-Za-z0-9]+)+).*[A-Za-z]+.*$',  # Your second pattern
    # Add any additional patterns here
]

# Background task example
@tasks.loop(seconds=60)  # Adjust the interval as needed
async def periodic_task():
    # Perform your periodic task here, e.g., cleaning up data or checking status
    print('Periodic task running...')

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    try:
        await bot.tree.sync()  # Synchronize slash commands globally
        logging.info("Slash commands synchronized globally.")
    except Exception as e:
        logging.error(f"Error synchronizing slash commands: {e}")
    periodic_task.start()  # Start the periodic task when the bot is ready

@bot.command()
async def ping(ctx):
    logging.info("Ping command received")  # Debug print
    try:
        await ctx.send('Pong!')
    except Exception as e:
        logging.error(f'Error sending ping response: {e}')

async def blocking_code(message):
    # Check if the message matches any pattern
    if any(re.search(pattern, message.content) for pattern in patterns):
        logging.info(f'Deleting message from {message.author}: {message.content}')  # Log the deletion
        await message.delete()  # Delete the message
        await message.channel.send('Your message was blocked due to inappropriate content.')  # Optional warning

@bot.slash_command(name='ping', description='Responds with Pong!')
async def ping_slash(interaction: nextcord.Interaction):
    await interaction.response.send_message('Pong!')

@bot.slash_command(name='botinfo', description='Get detailed information about the bot')
async def botinfo_slash(interaction: nextcord.Interaction):
    await interaction.response.defer()  # Acknowledge the interaction immediately

    bot_info = {
        'name': bot.user.name,
        'version': '1.0.0',  # Replace with your bot's version
        'status': 'Running',  # Replace with your bot's status
        'description': 'This bot does XYZ.',  # Add a description if needed
        'id': bot.user.id,
        'created_at': str(bot.user.created_at),
        'guilds': [guild.name for guild in bot.guilds],
        'prefix': bot.command_prefix,
        'latency': bot.latency
    }
    bot_info_json = json.dumps(bot_info, indent=2)
    if len(bot_info_json) > 2000:
        parts = [bot_info_json[i:i+1900] for i in range(0, len(bot_info_json), 1900)]
        await interaction.followup.send(f'```json\n{parts[0]}\n```')
        for part in parts[1:]:
            await interaction.followup.send(f'```json\n{part}\n```')
    else:
        await interaction.followup.send(f'```json\n{bot_info_json}\n```')

@bot.slash_command(name='serversettings', description='Get information about the server')
async def serversettings_slash(interaction: nextcord.Interaction):
    await interaction.response.defer()  # Acknowledge the interaction immediately

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
        'icon_url': str(guild.icon)  # Use 'icon' instead of 'icon_url'
    }
    server_settings_json = json.dumps(server_settings, indent=2)
    if len(server_settings_json) > 2000:
        # Split the response into multiple messages
        parts = [server_settings_json[i:i+1900] for i in range(0, len(server_settings_json), 1900)]
        await interaction.followup.send(f'```json\n{parts[0]}\n```')
        for part in parts[1:]:
            await interaction.followup.send(f'```json\n{part}\n```')
    else:
        await interaction.followup.send(f'```json\n{server_settings_json}\n```')

@bot.slash_command(name='backup', description='Backup server settings')
async def backup_slash(interaction: nextcord.Interaction):
    await interaction.response.defer()  # Acknowledge the interaction immediately

    guild = interaction.guild
    server_settings = {
        'name': guild.name,
        'id': guild.id,
        'member_count': guild.member_count,
        'roles': [{'name': role.name, 'permissions': role.permissions.value} for role in guild.roles if not role.managed],  # Convert permissions to integer
        'channels': [{'name': channel.name} for channel in guild.text_channels],
        'owner_id': guild.owner_id,
        'owner': str(guild.owner),
        'created_at': str(guild.created_at),
    }

    # Write the server settings to a backup file
    backup_filename = f'backup_{guild.id}.json'
    with open(backup_filename, 'w') as backup_file:
        json.dump(server_settings, backup_file, indent=2)

    await interaction.followup.send(f'Server settings have been backed up to {backup_filename}')

@bot.slash_command(name='restore', description='Restore the server settings from a backup')
async def restore_slash(interaction: nextcord.Interaction, backup_filename: str):
    await interaction.response.defer()  # Acknowledge the interaction immediately

    try:
        with open(backup_filename, 'r') as backup_file:
            server_settings = json.load(backup_file)

        # Restore server name
        guild = interaction.guild
        await guild.edit(name=server_settings['name'])

        # Restore roles
        for role_data in server_settings.get('roles', []):
            existing_role = nextcord.utils.get(guild.roles, name=role_data['name'])
            if existing_role is None:
                await guild.create_role(name=role_data['name'], permissions=nextcord.Permissions(role_data['permissions']))
            else:
                if not existing_role.managed:  # Check if the role is managed
                    await existing_role.edit(permissions=nextcord.Permissions(role_data['permissions']))

        # Restore channels
        for channel_data in server_settings.get('channels', []):
            existing_channel = nextcord.utils.get(guild.text_channels, name=channel_data['name'])
            if existing_channel is None:
                await guild.create_text_channel(name=channel_data['name'])

        await interaction.followup.send(f'Server settings have been restored from {backup_filename}')
    except FileNotFoundError:
        await interaction.followup.send(f'Backup file {backup_filename} not found')
    except Exception as e:
        await interaction.followup.send(f'An error occurred while restoring the backup: {e}')

@bot.slash_command(name='example', description='An example command')
async def example_command(interaction: nextcord.Interaction):
    await interaction.response.defer()  # Acknowledge immediately

    # Perform your operations here
    # Ensure they are efficient and do not block the event loop

    await interaction.followup.send('Operation completed successfully.')

@bot.slash_command(name='global_announcement', description='Send a global announcement to all servers')
async def global_announcement(interaction: nextcord.Interaction, message: str):
    await interaction.response.defer()  # Acknowledge the interaction immediately

    # Iterate through all guilds the bot is in
    for guild in bot.guilds:
        try:
            # Check if a notification channel already exists
            notification_channel = nextcord.utils.get(guild.text_channels, name="notifications")
            if notification_channel is None:
                # Create the notification channel if it doesn't exist
                notification_channel = await guild.create_text_channel(name="notifications")

            # Send the announcement message to the notification channel
            await notification_channel.send(f"📢 **Global Announcement:** {message}")
        except Exception as e:
            logging.error(f"Error sending announcement to guild {guild.name} ({guild.id}): {e}")

    await interaction.followup.send("Global announcement sent to all servers.")

# Define a rate limit (in seconds)
RATE_LIMIT = 1.0  # 1 second
last_message_time = 0  # Timestamp of the last processed message

@bot.event
async def on_message(message):
    global last_message_time

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Automod functionality
    await blocking_code(message)  # Use the blocking code

    # Implement rate limiting
    current_time = time.time()
    if current_time - last_message_time < RATE_LIMIT:
        return  # Skip processing if within rate limit
    last_message_time = current_time

    # Check for matches against defined patterns
    for pattern in patterns:
        if re.match(pattern, message.content):
            try:
                await message.delete()  # Delete the message from other users
                logging.info(f'Deleted message from {message.author}: {message.content}')
            except Exception as e:
                logging.error(f'Error deleting message from {message.author}: {e}')
            break  # Exit the loop after deleting the message

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
