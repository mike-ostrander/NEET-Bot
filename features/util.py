import json
from datetime import datetime


def write_to_json(content, filename):
    with open(filename, 'w') as outfile:
        json.dump(content, outfile)


def get_user(ctx, file, bot):
    server = get_server(ctx, file, bot)
    user = next(filter(lambda x: x["userId"] == ctx.author.id, server["users"]), None)
    if user is None:
        user = next(filter(lambda x: x["userId"] == ctx.author.id, server["users"]), None)
    return user


def get_server(ctx, file, bot):
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, file["servers"]), None)
    if server is None:
        file['servers'].append(add_server(ctx, file, bot))
    return file


async def validate_channel(msg, bot):
    try:
        if bot.get_channel(int(msg.content)) is not None:
            # file[key] = int(msg.content)
            return True
        elif bot.get_channel(int(msg.content)) is None:
            await msg.channel.send(
                "Invalid channel. Please enter valid channel ID or type 'exit' to cancel command.")
            msg = await bot.wait_for('message', check=lambda message: message.author == msg.author)
            await validate_channel(msg, bot)
    except ValueError:
        if msg.content.lower() == 'exit':
            await msg.channel.send("Command cancelled.")
            return False
        else:
            await msg.channel.send(
                "Invalid channel. Please enter valid channel ID or type 'exit' to cancel command.")
            msg = await bot.wait_for('message', check=lambda message: message.author == msg.author)
            await validate_channel(msg, bot)


def add_server(ctx, file, bot):
    if file['name'] == 'preferences':
        file['servers'].append({
            "serverId": ctx.guild.id,
            "commandPrefix": ".",
            "isAudit": False,
            "auditChannelId": 0,
            "isGreet": False,
            "greetChannelId": 0,
            "greetMsg": "Welcome to the server, {}",
        })
    elif file['name'] == 'xp':
        file['servers'].append({
            "serverId": ctx.guild.id,
            "isXp": True,
            "xpIgnoreChannels": 0,
            "users": [{
                "userId": bot.user.id,
                "userTotalXp": 4206900000000000000,
                "userLvl": 420690,
                "nextLvl": 0,
                "lastMsg": "2021-01-01T00:00:00.000000",
                "server": ctx.guild.id
            }]
        })
    elif file['name'] == 'birthday':
        file['servers'].append({
            "serverId": ctx.guild.id,
            "isBirthday": False,
            "birthdayMsg": "Happy birthday, {}!",
            "birthdayChannelId": 0,
            "users": [{
                "userId": bot.user.id,
                "userBirthday": "01-01",
                "userTz": 'GMT',
                "remindTime": "12:00",
                "server": ctx.guild.id
            }]
        })
    return file


def add_birthday(ctx, date, time, tz):
    if time == 0 or '':
        time = "12:00"
    return {
                "userId": ctx.author.id,
                "userBirthday": date,
                "userTz": tz,
                "remindTime": time,
                "server": ctx.guild.id
            }

