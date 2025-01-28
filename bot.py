import discord
from discord.ext import commands, tasks
from flask import Flask, request, jsonify, render_template
import threading
from dotenv import load_dotenv
import os
import requests
import json

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

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        try:
            await message.author.timeout(duration=180, reason="Automatic timeout for every message")
            await message.channel.send(f'{message.author.mention} has been timed out for 3 minutes.')
        except Exception as e:
            print(f'Error timing out {message.author}: {e}')

        await bot.process_commands(message)

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
