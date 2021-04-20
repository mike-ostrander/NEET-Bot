import os
import discord
from discord.ext import commands
from audit_feature import audit_message, audit_setup
import json

TOKEN = os.getenv('')
client = discord.Client()


def set_preferences():
    with open("preferences.json") as preferences_file:
        data = json.load(preferences_file)
    return data


preferences = set_preferences()
bot = commands.Bot(command_prefix=preferences['commandPrefix'])


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    # if message.content.startswith(bot.command_prefix):
    #     await messsage.channel.send('Hello!')
    if preferences['auditIsActive']:
        audit_message(message, preferences['audit_channel'])
    if message.content.startsWith(bot.command_prefux+'set audit'):
        audit_setup(preferences)


client.run(TOKEN)