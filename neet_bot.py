from discord.ext.commands import Bot, errors
from discord import Member
# from discord import guild
import json
import random
from features.xp import add, populate_exist
import os.path
from os import path
from features.xp import xp_process, populate_new
from features.util import *


bot = Bot(command_prefix='.')
TOKEN = load_from_json("json/auth.json")['token']
error_handling = errors


@bot.event
async def on_ready():
    print('{0.user} is now active.'.format(bot))


@bot.event
async def on_message(ctx):
    # Loads the files for the specific server it gets the message from
    pref_name = 'json/preferences-{}.json'.format(ctx.guild.id)
    xp_name = 'json/xp-{}.json'.format(ctx.guild.id)
    preferences = check_server_file(ctx, pref_name, 'preferences', bot.user.id)
    xp = check_server_file(ctx, xp_name, 'xp', bot.user.id)
    print('Server: {0.guild}\n{0.created_at} {0.author}: {0.content}'.format(ctx))
    # Checks if the incoming message is from the bot, and if it is, it will ignore it.
    if ctx.author == bot.user:
        return
    # If the audit is active, the bot will send a copy of the incoming message to the designated audit channel
    if preferences['auditIsActive']:
        try:
            timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
            channel = bot.get_channel(preferences['auditChannel'])
            await channel.send(
                f'{timestamp}\n{ctx.author.mention} in {ctx.channel.mention}: \n{ctx.content}')
        except AttributeError:
            print("No audit channel set.")
    write_to_json(await xp_process(ctx, xp), xp['path'])
    await bot.process_commands(ctx)


@bot.event
async def on_member_join(member):
    pref_name = 'json/preferences-{}.json'.format(member.guild.id)
    xp_name = 'json/xp-{}.json'.format(member.guild.id)
    preferences = check_server_file(member, pref_name, 'preferences', bot.user.id)
    xp = check_server_file(member, xp_name, 'xp', bot.user.id)
    if preferences['isGreet']:
        channel = bot.get_channel(preferences['auditChannel'])
        await channel.send('Welcome to the server, {}!'.format(member.id.mention))
    write_to_json(populate_new(member, xp), xp['path'])


@bot.event
async def on_message_delete(ctx, pref):
    if ctx.author == bot.user:
        return
    if pref['auditIsActive']:
        timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
        channel = bot.get_channel(pref['auditChannel'])
        await channel.send(f'{timestamp}\n{ctx.author.mention} in {ctx.channel.mention}: \n{ctx.content}')


@bot.event
async def on_message_edit(old_msg, new_msg, pref):
    if old_msg.author == bot.user:
        return
    if pref['auditIsActive']:
        created = old_msg.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
        edited = new_msg.edited_at.strftime("%m/%d/%Y %I:%M:%S%p")
        channel = bot.get_channel(pref['auditChannel'])
        await channel.send(
            f'ORIGINAL:\n{created}\n{old_msg.author.mention} in {old_msg.channel.mention}: \n{old_msg.content}\n'
            f'EDITED:\n{edited}\n{new_msg.author.mention} in {new_msg.channel.mention}: \n'
            f'{new_msg.content}')


@bot.command()
async def audit(ctx):
    print('{0.author} used the audit command in {0.channel}.'.format(ctx))
    pref = check_server_file(ctx, 'json/preferences-{}.json'.format(ctx.guild.id), 'preferences', bot.user.id)
    if pref['auditIsActive']:
        await ctx.channel.send(
            "The audit feature is enabled. Disable or change channel? (Disable, Change, or Exit)")
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() == "change":
            await ctx.channel.send("Please send the channel ID of where the audit will be changed to.")
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            channel_id = await validate_channel(msg, bot)
            if channel_id != 'cancelled':
                pref['auditChannel'] = channel_id
                await ctx.channel.send("Channel changed.")
            else:
                await ctx.channel.send("Command cancelled.")
        elif msg.content.lower() == "disable":
            pref['auditIsActive'] = False
            pref['auditChannel'] = ''
            await ctx.channel.send("Audit disabled.")
        elif msg.content.lower() == "exit":
            await ctx.channel.send("Command cancelled.")
    elif not pref['auditIsActive']:
        await ctx.channel.send("The audit feature is currently disabled. Would you like to enable? (Y/Yes or N/No)")
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() == "y" or msg.content.lower() == "yes":
            await ctx.channel.send("Please send the channel ID of where the audit will be recorded.")
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            channel_id = await validate_channel(msg, bot)
            if channel_id != 'cancelled':
                pref['auditChannel'] = channel_id
                pref['auditIsActive'] = True
                await ctx.channel.send("Audit successfully setup.")
            else:
                await ctx.channel.send("Channel changed.")
        if msg.content.lower() == "n" or msg.content.lower() == "no":
            await ctx.channel.send("Command cancelled.")
    with open(pref['path'], 'w') as outfile:
        json.dump(pref, outfile)
    load_from_json(pref['path'])
    return


@bot.command()
async def ping(ctx):
    await ctx.channel.send("pong")


@bot.command()
async def roll(ctx, arg):
    req = arg.split('d')
    dice = int(req[0])
    sides = int(req[1])
    x = 1
    total = 0
    rolls = ''
    while x <= dice:
        result = random.randint(1, sides)
        total += result
        if x == 1:
            rolls = '{}'.format(result)
        else:
            rolls = '{}, {}'.format(rolls, result)
        x += 1
    await ctx.channel.send('{}  ({})'.format(total, rolls))
    return


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return
    error = getattr(error, 'original', error)
    if isinstance(error, errors.MissingRequiredArgument):
        if ctx.message.content.lower() == '.roll':
            await ctx.channel.send('Please format in a (x)d(y) format, where x = number of dice '
                                   'and y = how many sides on each dice. Ex: .roll 1d20.')
        return


@bot.command()
async def lvl(ctx, member: Member = None):
    xp = load_from_json('json/xp-{}.json'.format(ctx.guild.id))
    if member is None:
        member = ctx.author
    user = get_user(member.id, xp)
    await ctx.channel.send('{} is currently level {} ({}/{}EXP)'.format(
        member.display_name, user['userLvl'], user['userTotalXp'], user['nextLvl']))


bot.run(TOKEN)
