import asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import date
from discord.ext.commands import Bot, errors, has_permissions
from discord import Member
import json
import random
from features.xp import xp_process, populate_new
from features.util import *
from features.timezone import convert_time

bot = Bot(command_prefix='.')
error_handling = errors
scheduler = BlockingScheduler()


def load_from_json(filename):
    try:
        with open('json/{}.json'.format(filename)) as file:
            data = json.load(file)
    except FileNotFoundError:
        create_file(filename)
        data = load_from_json(filename)
    return data


def create_file(name):
    filename = 'json/{}.json'.format(name)
    contents = {
        "path": filename,
        "name": name,
        "servers": []
    }
    with open('json/{}.json'.format(name), 'w') as outfile:
        json.dump(contents, outfile)
    return


preferences = load_from_json('preferences')
TOKEN = load_from_json("auth")['token']
xp_data = load_from_json('xp')
birthdays = load_from_json('birthday')


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
    await birthday_check()
    for server in preferences['servers']:
        if server['isGreet'] is True:
            channel = bot.get_channel(server['greetChannelId'])
            await channel.send('{0.user.mention} has woken up!'.format(bot))


@bot.event
async def on_message(ctx):
    global bot
    # Loads the files for the specific server it gets the message from
    print('Server: {0.guild}\n{0.created_at} {0.author}: {0.content}'.format(ctx))
    pref = preferences
    xp = xp_data
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
    if server is None:
        pref = add_server(ctx, pref, bot)
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, pref["servers"]), None)
        write_to_json(preferences, 'json/preferences.json')
        load_globals('preferences')
    # Checks if the incoming message is from the bot, and if it is, it will ignore it.
    if ctx.author == bot.user:
        return
    # If the audit is active, the bot will send a copy of the incoming message to the designated audit channel
    if server['isAudit']:
        try:
            timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
            channel = bot.get_channel(server['auditChannelId'])
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
        channel = bot.get_channel(server['greetChannelId'])
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
    if server['isAudit']:
        timestamp = ctx.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
        channel = bot.get_channel(server['auditChannelId'])
        await channel.send(f'{timestamp}\n{ctx.author.mention} in {ctx.channel.mention}: \n{ctx.content}')


@bot.event
async def on_message_edit(old_msg, new_msg):
    pref = get_server(old_msg, preferences, bot)
    if old_msg.author == bot.user:
        return
    if pref['isAudit']:
        created = old_msg.created_at.strftime("%m/%d/%Y %I:%M:%S%p")
        edited = new_msg.edited_at.strftime("%m/%d/%Y %I:%M:%S%p")
        channel = bot.get_channel(pref['auditChannelId'])
        await channel.send(
            f'ORIGINAL:\n{created}\n{old_msg.author.mention} in {old_msg.channel.mention}: \n{old_msg.content}\n'
            f'EDITED:\n{edited}\n{new_msg.author.mention} in {new_msg.channel.mention}: \n'
            f'{new_msg.content}')


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
    if server['isXp']:
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
    if server['isXp']:
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
async def tz(ctx, dt_time, old_tz, new_tz):
    if dt_time is None or old_tz is None or new_tz is None:
        await ctx.channel.send('The correct format is: `HH:MM OLD_TIMEZONE NEW_TIMEZONE`\n'
                               'Example: `14:30 PST GDT` or `09:45PM EST GMT`')
        return
    converted_time = convert_time(dt_time, old_tz, new_tz)
    await ctx.channel.send('{} {} is {} {}'.format(dt_time, old_tz, converted_time.strftime("%I:%M%p"), new_tz))


@bot.command()
@has_permissions(administrator=True)
async def setup(ctx, arg: str = None):
    async def channel_prompt():
        await ctx.channel.send('Please enter the channel ID of where the related messages will be sent.')
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if await validate_channel(msg, bot):
            await ctx.channel.send('{} tracking has been enabled.'.format(arg.capitalize()))
            server['{}ChannelId'.format(arg.lower())] = int(msg.content)
            return True
        else:
            return False

    async def message_prompt():
        await ctx.channel.send('Please enter the message.\n'
                               'To include a mention, use {} at your preferred location.\n'
                               'To cancel, enter `cancel` instead')
        msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() != 'cancel':
            server['{}Msg'.format(arg.lower())] = msg.content
            await ctx.channel.send('The message has been successfully changed.')
        else:
            await ctx.channel.send('Command cancelled.')
        return

    async def setup_prompts(has_channel, has_message):
        if server['is{}'.format(arg.capitalize())]:
            if has_channel and has_message:
                channel = bot.get_channel(server['{}ChannelId'.format(arg.lower())])
                await ctx.channel.send('{} tracking currently enabled.'
                                       '\nThe current message is: `{}`'
                                       '\nThe channel is set to {}'
                                       '\nWould you like to `disable` the feature, '
                                       '`edit` the message, or '
                                       '`change` the channel?'
                                       .format(arg.capitalize(),
                                               server['{}Msg'.format(arg.lower())],
                                               channel.mention))
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if msg.content.lower() == 'disable':
                    server['is{}'.format(arg.capitalize())] = False
                elif msg.content.lower() == 'edit':
                    await message_prompt()
                elif msg.content.lower() == 'change':
                    await channel_prompt()
                else:
                    await ctx.channel.send('Command cancelled.')
            elif has_channel and not has_message:
                channel = bot.get_channel(server['{}ChannelId'.format(arg.lower())])
                await ctx.channel.send('{} tracking currently enabled.'
                                       '\nThe channel is set to {}'
                                       '\nWould you like to `disable` the feature or '
                                       '`change` the channel?'
                                       .format(arg.capitalize(),
                                               channel.mention))
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if msg.content.lower() == 'disable':
                    server['is{}'.format(arg.capitalize())] = False
                elif msg.content.lower() == 'change':
                    await channel_prompt()
                else:
                    await ctx.channel.send('Command cancelled.')
            elif not has_channel and not has_message:
                await ctx.channel.send('{} tracking currently enabled.'
                                       '\nWould you like to `disable` the feature?'
                                       .format(arg.capitalize()))
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if msg.content.lower() == 'disable' or msg.content.lower() == 'yes' or msg.content.lower() == 'y':
                    server['is{}'.format(arg.capitalize())] = False
                    await ctx.channel.send('{} tracking has been disabled.'.format(arg.capitalize()))
                else:
                    await ctx.channel.send('Command cancelled.')
            return
        else:
            await ctx.channel.send('{} tracking is currently disabled. Would you like to `enable`?'
                                   .format(arg.capitalize()))
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            if msg.content.lower() == 'enable' or msg.content.lower() == 'yes' or msg.content.lower() == 'y':
                if has_channel and not has_message:
                    await channel_prompt()
                elif has_message and has_channel:
                    def_msg = '{}Msg'.format(arg.lower())
                    await ctx.channel.send('The message is: ```{}```Would you like to `change` it?'
                                           .format(server[def_msg]))
                    msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                    if msg.content.lower() == 'change':
                        await message_prompt()
                    server['is{}'.format(arg.capitalize())] = True
                    await channel_prompt()
                    return
                else:
                    server['is{}'.format(arg.capitalize())] = True
                    await ctx.channel.send('{} tracking has been enabled.'.format(arg.capitalize()))
            else:
                await ctx.channel.send('Command cancelled.')

    if arg is None:
        await ctx.channel.send('The commands available are: `birthday`, `xp`, `greet`, and `cancel`')
        arg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        arg = arg.content
    if arg.lower() == 'birthday':
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, birthdays["servers"]), None)
        if server is None:
            add_server(ctx, birthdays, bot)
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, birthdays["servers"]), None)
        await setup_prompts(True, True)
        write_to_json(birthdays, 'json/birthday.json')
        load_globals('birthday')
    elif arg.lower() == 'xp':
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp_data["servers"]), None)
        await setup_prompts(False, False)
        write_to_json(xp_data, 'json/xp.json')
        load_globals('xp')
    elif arg.lower() == 'audit':
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
        await setup_prompts(True, False)
        write_to_json(preferences, 'json/preferences.json')
        load_globals('preferences')
    elif arg.lower() == 'greet':
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
        await setup_prompts(True, True)
        write_to_json(preferences, 'json/preferences.json')
        load_globals('preferences')
    # elif arg.lower() == 'prefix':
    #     server = next(filter(lambda x: x["serverId"] == ctx.guild.id, preferences["servers"]), None)
    #     await ctx.channel.send('The current prefix is `{}` Would you like to `change` it?'
    #                            .format(server['commandPrefix']))
    #     msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    #     if msg.content.lower() == 'change' or msg.content.lower() == 'y' or msg.content.lower() == 'yes':
    #         await ctx.channel.send('Enter the new prefix:')
    #         msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    #         server['commandPrefix'] = msg.content
    #         await ctx.channel.send('The prefix has been changed to `{}`'.format(server['commandPrefix']))
    #         write_to_json(preferences, 'json/preferences.json')
    #         load_globals('preferences')
    #     else:
    #         await ctx.channel.send('Command cancelled')
    else:
        return


@bot.command()
async def birthday(ctx):
    # b_day = get_server(ctx, birthdays, bot)
    # server = next(filter(lambda x: x["serverId"] == ctx.guild.id, b_day["servers"]), None)
    empty_list = ['server', 'userBirthday', 'userTz', 'userId', 'remindTime']

    async def get_date():
        await ctx.channel.send(
            'Please enter the month of your birthday.\nExample: `01`')
        msg_month = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        month = msg_month.content
        await ctx.channel.send(
            'Please enter the day of your birthday.\nExample: `05`')
        msg_day = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        day = msg_day.content
        await ctx.channel.send('Please enter the time. To use the default (12PM), just type 0.\n'
                               'Example: `14:30` or `09:45PM`')
        msg_time = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        dt_time = msg_time.content
        await ctx.channel.send('Please enter your timezone.\nExample: `GMT`')
        msg_tz = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        timezone = msg_tz.content
        return ['{}-{}'.format(month, day), dt_time, timezone]

    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, birthdays["servers"]), None)
    if server['isBirthday']:
        user = next(filter(lambda x: x["userId"] == ctx.author.id, server["users"]), None)
        if user is not None and user['userId'] == ctx.author.id:
            await ctx.channel.send('Your current birthday is set as {} {} {} . Options: `change`, `remove`'
                                   .format(user['userBirthday'], user['remindTime'], user['userTz']))
            msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            if msg.content.lower() == 'change':
                await ctx.channel.send('Would you like to `change` the details of your birthday? Yes/No')
                msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
                if msg.content.lower() == 'yes' or msg.content.lower() == 'y' or msg.content.lower() == 'change':
                    temp_list = await get_date()
                    user['userBirthday'] = temp_list[0]
                    user['remindTime'] = temp_list[1]
                    user['userTz'] = temp_list[2]
                    await ctx.channel.send('Birthday successfully changed.')
                    write_to_json(birthdays, 'json/birthday.json')
                    load_globals('birthday')
            elif msg.content.lower() == 'remove':
                for field in empty_list:
                    user[field] = ''
                    if field in user and not user[field]:
                        user.pop(field)
                await ctx.channel.send('Birthday removed.')
                write_to_json(birthdays, 'json/birthday.json')
                load_globals('birthday')
        elif user is None:
            temp_list = await get_date()
            birthday_entry = add_birthday(ctx, temp_list[0], temp_list[1], temp_list[2])
            await ctx.channel.send('Birthday successfully added.')
            server['users'].append(birthday_entry)
            write_to_json(birthdays, 'json/birthday.json')
            load_globals('birthday')


async def birthday_check():
    today = date.today()
    now = datetime.utcnow()
    while True:
        for server in birthdays['servers']:
            if server['isBirthday']:
                for user in server['users']:
                    birth_date = datetime.strptime(user['userBirthday'], '%m-%d')
                    birth_date = birth_date.strftime("%m-%d")
                    if birth_date == today.strftime("%m-%d"):
                        remind_time = datetime.strptime(user['remindTime'], '%H:%M')
                        current_hour = datetime.strptime(convert_time(now, 'UTC', 'EDT'), '%H:%M')
                        if current_hour.hour == remind_time.hour:
                            channel = bot.get_channel(server['birthdayChannelId'])
                            member = bot.get_user(user['userId'])
                            await channel.send(server['birthdayMsg'].format(member.mention))
        await asyncio.sleep(3600)

bot.run(TOKEN)
