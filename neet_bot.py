from discord.ext.commands import Bot
from audit_feature import audit_message
import json


def load_from_json(filename):
    global preferences
    with open(filename) as preferences_file:
        data = json.load(preferences_file)
    return data


preferences = load_from_json("preferences.json")
bot = Bot(command_prefix=preferences['commandPrefix'])
TOKEN = load_from_json("auth.json")['token']


@bot.event
async def on_ready():
    print('{0.user} is now active.'.format(bot))
    validate_channel(preferences['auditChannel'])


@bot.event
async def on_message(message):
    print('{0.created_at} {0.author}: {0.content}'.format(message))
    if message.author == bot.user:
        return
    if preferences['auditIsActive']:
        audit_message(message, preferences['auditChannel'])
    # if not preferences['auditIsActive']:
    #     return
    await bot.process_commands(message)


@bot.command()
async def audit(ctx):
    pref = preferences
    print('{0.author} used the audit command in {0.channel}.'.format(ctx))
    if pref['auditIsActive']:
        await ctx.channel.send("The audit feature is enabled. Disable or change channel? (Disable, Change, or Exit)")
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() == "change":
            await ctx.channel.send("Please send the channel ID of where the audit will be changed to.")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            pref['auditChannel'] = response.content
            await ctx.channel.send("Channel changed.")
        if msg.content.lower() == "disable":
            pref['auditIsActive'] = False
            pref['auditChannel'] = ''
            await ctx.channel.send("Audit disabled.")
        if msg.content.lower() == "exit":
            await ctx.channel.send("Command cancelled.")
            return
    elif not pref['auditIsActive']:
        await ctx.channel.send("The audit feature is currently disabled. Would you like to enable? (Y/Yes or N/No)")
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() == "y" or msg.content.lower() == "yes":
            pref['auditIsActive'] = True
            await ctx.channel.send("Please send the channel ID of where the audit will be recorded.")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            pref['auditChannel'] = response.content
            await ctx.channel.send("Channel set, audit log is now active.")
        if msg.content.lower() == "n" or msg.content.lower() == "no":
            await ctx.channel.send("Command cancelled.")
            return

    with open('preferences.json', 'w') as outfile:
        json.dump(pref, outfile)
    load_from_json('preferences.json')
    validate_channel(preferences['auditChannel'])
    return


def validate_channel(channel_id):

    return


@bot.command()
async def ping(ctx):
    await ctx.channel.send("pong")


bot.run(TOKEN)
