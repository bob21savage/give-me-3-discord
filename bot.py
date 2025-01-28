import discord
from discord.ext import commands, tasks
from discord.utils import utcnow
from flask import Flask, request, jsonify, render_template
import threading
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, timedelta
import re

load_dotenv()  # Load environment variables from .env file
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Get the token from the environment
print(f'DISCORD_TOKEN: {DISCORD_TOKEN}')  # Print the token for debugging

CLIENT_ID = os.getenv('ClientID')
CLIENT_SECRET = os.getenv('ClientSecret')

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/auth/discord/redirect', methods=['GET'])
def discord_redirect():
    code = request.args.get('code')
    if code:
        form_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': 'http://localhost:1500/api/auth/discord/redirect'
        }

        response = requests.post('https://discord.com/api/v10/oauth2/token', data=form_data)
        output = response.json()

        if 'access_token' in output:
            access_token = output['access_token']
            user_info_response = requests.get('https://discord.com/api/v10/users/@me', headers={
                'Authorization': f'Bearer {access_token}'
            })
            user_info = user_info_response.json()
            return jsonify(user_info)

    return jsonify({'error': 'No code provided'}), 400

def run_flask():
    app.run(host='0.0.0.0', port=1500)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    intents = discord.Intents.default()
    intents.messages = True
    intents.members = True  # Add this line to enable member intents

    bot = commands.Bot(command_prefix='!', intents=intents)

    patterns = [
        r'^.*([A-Za-z0-9]+( [A-Za-z0-9]+)+).*[A-Za-z]+.*$',
        r'^<#(?<id>\d{17,20})>$',
        r'(?<subdomain>\w+)\.?(?<hostname>dis(?:cord)?(?:app|merch|status)?)\.(?<tld>com|g(?:d|g|ift)|(?:de(?:sign|v))|media|new|store|net)',
        r'[a4]?+\s*[b8]+\s*c+\s*d+\s*[e3]?+\s*f+\s*[g9]+\s*h+\s*[i1l]?+\s*j+\s*k+\s*[l1i]+\s*(m|nn|rn)+\s*n+\s*[o0]?+\s*p+\s*q+\s*r+\s*[s5]+\s*[t7]+\s*[uv]?+\s*v+\s*(w|vv|uu)+\s*x+\s*y+\s*z+\s*0+\s*9+\s*8+\s*7+\s*6+\s*5+\s*4+\s*3+\s*2+\s*1+','
        r'^https?:\/\/',
        r'^<@&(?<id>\d{17,20})>$',
        r'^<@!?(?<id>\d{17,20})>$',
        r'^wss?:\/\/',
        r'(?<url>^https:\/\/(?:(?:canary|ptb).)?discord(?:app)?.com\/api(?:\/v\d+)?\/webhooks\/(?<id>\d+)\/(?<token>[\w-]+)\/?$)',
        r'[^\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]'
    ]

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')

    @bot.event
    async def on_message(message):
        # Ignore messages from the bot itself
        if message.author == bot.user:
            return

        # Check if the message matches any of the regex patterns
        for pattern in patterns:
            if re.match(pattern, message.content):
                await message.delete()  # Delete the message
                break  # Exit the loop after deleting

        # Check if the bot has permission to timeout the user
        if message.author.top_role >= message.guild.me.top_role:
            await message.channel.send("I cannot timeout this user because my role is lower.")
            return

        # Set the duration for the timeout (e.g., 3 minutes)
        timeout_duration = timedelta(minutes=3)
        timeout_until = utcnow() + timeout_duration  # Use utcnow() for an aware datetime

        try:
            await message.author.timeout(timeout_until, reason="Automatic timeout for every message")
            await message.channel.send(f'{message.author.mention} has been timed out for 3 minutes.')
        except Exception as e:
            print(f'Error timing out {message.author}: {e}')

        await bot.process_commands(message)  # Process other commands if any

    @bot.command(name='ping')
    async def ping(ctx):
        await ctx.send('Pong!')

    @bot.command(name='botinfo')
    async def botinfo(ctx):
        bot_info = {
            'username': bot.user.username,
            'id': bot.user.id,
            'created_at': str(bot.user.created_at),
            'guilds': [guild.name for guild in bot.guilds]
        }
        await ctx.send(f'```json\n{json.dumps(bot_info, indent=2)}\n```')

    @bot.command(name='serversettings')
    async def serversettings(ctx):
        guild = ctx.guild
        server_settings = {
            'name': guild.name,
            'id': guild.id,
            'member_count': guild.member_count,
            'roles': [role.name for role in guild.roles],
            'channels': [channel.name for channel in guild.channels]
        }
        await ctx.send(f'```json\n{json.dumps(server_settings, indent=2)}\n```')

    bot.run(DISCORD_TOKEN)
