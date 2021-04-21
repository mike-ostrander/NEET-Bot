from discord.ext.commands import Bot
from audit_feature import audit_message
import json


def load_from_json(filename):
    with open(filename) as preferences_file:
        data = json.load(preferences_file)
    return data


preferences = load_from_json("preferences.json")
bot = Bot(command_prefix=preferences['commandPrefix'])
TOKEN = load_from_json("auth.json")['token']


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_message(message):
    print('{0.created_at} {0.author}: {0.content}'.format(message))
    if message.author == bot.user:
        return
    if preferences['auditIsActive']:
        audit_message(message, '.')
    # if not preferences['auditIsActive']:
    #     return
    await bot.process_commands(message)


@bot.command()
async def audit(ctx):
    print('{0.author} used the audit command in {0.channel}.'.format(ctx))
    if preferences['auditIsActive']:
        await ctx.channel.send("The audit feature is already enabled. Would you like to disable?")
        return
    if not preferences['auditIsActive']:
        await ctx.channel.send("The audit feature is currently disabled. Would you like to enable?")
        return


@bot.command()
async def ping(ctx):
    await ctx.channel.send("pong")


bot.run(TOKEN)
