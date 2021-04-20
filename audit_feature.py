import discord
from discord.ext import commands

client = discord.Client()


def audit_message(message, channel):
    if channel == '':
        print('There is no audit channel currently ')
    print(message)
    print(channel)


def audit_setup(preferences):
    if not preferences['auditIsActive']:
        print("")