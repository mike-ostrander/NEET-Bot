from discord.ext.commands import Bot, errors
from discord import Member
import json
import random
from features.xp import xp_process, populate_new
from features.util import *
from features.timezone import convert_time

bot = Bot(command_prefix='.')
error_handling = errors


def load_from_json(filename):
    try:
        with open('json/{}.json'.format(filename)) as file:
            data = json.load(file)
    except FileNotFoundError:
        create_file(filename)
        data = load_from_json(filename)

    return data


def create_file(name):
    contents = None
    filename = 'json/{}.json'.format(name)
    if name == 'preferences':
        contents = {
            "path": filename,
            "name": name,
            "servers": []
        }
    elif name == 'xp':
        contents = {
            "path": filename,
            "name": name,
            "servers": []}
    with open('json/{}.json'.format(name), 'w') as outfile:
        json.dump(contents, outfile)
    return


preferences = load_from_json('preferences')
TOKEN = load_from_json("auth")['token']
xp_data = load_from_json('xp')


def load_globals(name):
    global preferences
    global xp_data
    if name == 'preferences':
        preferences = load_from_json('preferences')
    elif name == 'xp':
        xp_data = load_from_json('xp')


@bot.event
async def on_ready():
    print('{0.user} is now active.'.format(bot))
    for server in preferences['servers']:
        if server['isGreet'] is True:
            channel = bot.get_channel(server['greetChannel'])
            await channel.send('{0.user.mention} has woken up!'.format(bot))


@bot.event
async def on_message(ctx):
    # Loads the files for the specific server it gets the message from
    print('Server: {0.guild}\n{0.created_at} {0.author}: {0.content}'.format(ctx))
    pref = preferences
    xp = xp_data
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
    if server is None:
        pref = add_server(ctx, pref, bot)
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, pref["servers"]), None)
        # pref['servers'].append(server)
        write_to_json(preferences, 'json/preferences.json'.format(ctx.guild.id))
        load_globals('preferences')
    # Checks if the incoming message is from the bot, and if it is, it will ignore it.
    if ctx.author == bot.user:
        return
    # If the audit is active, the bot will send a copy of the incoming message to the designated audit channel
    if server['auditIsActive']:
        try:
            timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
            channel = bot.get_channel(server['auditChannel'])
            await channel.send(
                f'{timestamp}\n{ctx.author.mention} in {ctx.channel.mention}: \n{ctx.content}')
        except AttributeError:
            print("No audit channel set.")
    write_to_json(await xp_process(ctx, xp, bot), xp['path'])
    load_globals('xp')
    await bot.process_commands(ctx)


@bot.event
async def on_member_join(member):
    pref = get_server(member, preferences, bot)
    server = next(filter(lambda x: x["serverId"] == member.guild.id, pref["servers"]), None)
    if server['isGreet']:
        channel = bot.get_channel(server['greetChannel'])
        if '{}' in server['greetMsg']:
            await channel.send(server['greetMsg'].format(member.id.mention))
        else:
            await channel.send(server['greetMsg'])
    write_to_json(await populate_new(member, xp_data, bot), xp_data['path'])
    load_globals('xp')


@bot.event
async def on_message_delete(ctx):
    pref = get_server(ctx, preferences, bot)
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, pref["servers"]), None)
    if ctx.author == bot.user:
        return
    if server['auditIsActive']:
        timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
        channel = bot.get_channel(server['auditChannel'])
        await channel.send(f'{timestamp}\n{ctx.author.mention} in {ctx.channel.mention}: \n{ctx.content}')


@bot.event
async def on_message_edit(old_msg, new_msg):
    pref = get_server(old_msg, preferences, bot)
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
    pref = get_server(ctx, preferences, bot)
    print('{0.author} used the audit command in {0.channel}.'.format(ctx))
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
    load_from_json(pref['name'])
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
    xp = get_server(ctx, xp_data, bot)
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp["servers"]), None)
    if member is None:
        member = ctx.author
        intro = 'You are'
    else:
        intro = '{} is'.format(member.display_name)
    user = next(filter(lambda x: x["userId"] == member.id, server["users"]), None)
    await ctx.channel.send('{} currently level {} ({}/{}EXP)'.format(
        intro, user['userLvl'], user['userTotalXp'], user['nextLvl']))


@bot.command()
async def top(ctx, arg: int = None):
    xp = get_server(ctx, xp_data, bot)
    user_list = []
    leaderboard = 'Top {}:'.format(arg)
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp["servers"]), None)
    for user in server['users']:
        if bot.user.id != user['userId']:
            user_list.append([user['userId'], user['userTotalXp']])
    user_list.sort(reverse=True, key=lambda x: x[1])
    if arg is None:
        arg = 10
        leaderboard = 'Top {}:'.format(10)
    if arg >= len(user_list):
        arg = len(user_list)
    y = 0
    while y < arg:
        leaderboard = '{}\n{}. {}\t{}'.format(leaderboard, (y + 1), await bot.fetch_user(user_list[y][0]),
                                              user_list[y][1])
        y += 1
    print(leaderboard)
    await ctx.channel.send('```{}```'.format(leaderboard))


@bot.command()
async def say(ctx, arg):
    await ctx.message.delete()
    await ctx.channel.send(arg)


@bot.command()
async def greet(ctx, arg: str = None):
    pref = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
    if arg is None:
        await ctx.channel.send('The commands available are: enable, disable, channel, and message')
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        arg = msg.content
    if pref['isGreet']:
        if arg.lower() == 'channel':
            await ctx.channel.send('The current greeting channel is {}. Would you like to change it? Y/N'
                                   .format(pref['greetChannel']))
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
                await ctx.channel.send('Please enter the channel ID of the new channel.')
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                res = await validate_channel(msg, bot)
                if res == 'cancelled':
                    await ctx.channel.send('Command cancelled.')
                    return
                else:
                    pref['greetChannel'] = res
                    await ctx.channel.send('Greeting channel changed.')
        elif arg.lower() == 'message':
            await ctx.channel.send('The current greeting is {}. Would you like to change it? Y/N'
                                   .format(pref['greetMsg']))
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            if msg.content.lower() == 'y' or msg.content.lower() == 'yes':
                await ctx.channel.send('Please enter the new greeting or cancel to exit. To include the new member, '
                                       'simply put {} where you want it at.')
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if msg.content == 'cancel':
                    await ctx.channel.send('Default message kept.')
                else:
                    pref['greetMsg'] = msg.content
                    await ctx.channel.send('New message set.')
        elif arg.lower() == 'disable':
            pref['isGreet'] = False
            await ctx.channel.send('Greeting is disabled.')
        elif arg.lower() == 'enable':
            await ctx.channel.send('The greeting function is already enabled.')
            return
    else:
        if arg.lower() == 'enable':
            await ctx.channel.send('Please enter the channel ID for the greeting to go.')
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            res = await validate_channel(msg, bot)
            if res == 'cancelled':
                await ctx.channel.send('Command cancelled.')
                return
            else:
                pref['greetChannel'] = res
                await ctx.channel.send('The default  greeting is {}.\n'
                                       'Please enter a greeting or cancel to exit. To include the new member, '
                                       'simply put {{}} where you want it at.'.format(pref['greetMsg']))
                res = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if res.content == 'cancel':
                    await res.channel.send('Command cancelled.')
                    return
                pref['greetMsg'] = res.content
                pref['isGreet'] = True
                await ctx.channel.send('Greeting successfully set up.')
    write_to_json(preferences, 'json/preferences.json'.format(ctx.guild.id))
    load_globals('preferences')
    return


@bot.command()
async def tz(ctx, time, old_tz, new_tz):
    if time is None or old_tz is None or new_tz is None:
        await ctx.channel.send('The correct format is: `HH:MM OLD_TIMEZONE NEW_TIMEZONE`\n'
                               'Example: `14:30 PST GDT` or `09:45PM EST GMT`')
        return
    converted_time = convert_time(time, old_tz, new_tz)
    await ctx.channel.send('{} {} is {} {}'.format(time, old_tz, converted_time, new_tz))

bot.run(TOKEN)
