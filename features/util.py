import json


def write_to_json(content, filename):
    with open(filename, 'w') as outfile:
        json.dump(content, outfile)
    load_from_json(filename)


def check_server_file(ctx, name, bot):
    contents = None
    filename = 'json/{}-{}.json'.format(name, ctx.guild.id)
    try:
        return load_from_json(filename)
    except FileNotFoundError:
        if name == 'preferences':
            contents = {"path": filename, "serverId": ctx.guild.id, "commandPrefix": ".",
                        "auditIsActive": False, "auditChannel": 0, "isGreet": False, "greetChannel": 0,
                        "greatMsg": "Welcome to the server, {}"}
        elif name == 'xp':
            contents = {"path": filename, "serverId": ctx.guild.id, "xpEnabled": True, "xpIgnoreChannels": 0,
                        "users": [{
                            "userId": bot.user.id,
                            "userTotalXp": 4206900000000000000,
                            "userLvl": 420690,
                            "nextLvl": 0,
                            "lastMsg": "2021-01-01T00:00:00.000000",
                            "server": ctx.guild.id
                        }]}
        with open(filename, 'w') as outfile:
            json.dump(contents, outfile)
        return load_from_json(filename)


def get_user(user_id, xp):
    server = next(filter(lambda x: x["serverId"] == xp['serverId'], xp["servers"]), None)
    user = next(filter(lambda x: x["userId"] == user_id, server["users"]), None)
    return user


def load_from_json(filename):
    with open(filename) as file:
        data = json.load(file)
    return data


async def validate_channel(msg, bot):
    try:
        if bot.get_channel(int(msg.content)) is not None:
            # file[key] = int(msg.content)
            return int(msg.content)
        elif bot.get_channel(int(msg.content)) is None:
            await msg.channel.send(
                "Invalid channel. Please enter valid channel ID or type 'exit' to cancel command.")
            msg = await bot.wait_for('message', check=lambda message: message.author == msg.author)
            await validate_channel(msg, bot)
    except ValueError:
        if msg.content.lower() == 'exit':
            await msg.channel.send("Command cancelled.")
            return 'cancelled'
        else:
            await msg.channel.send(
                "Invalid channel. Please enter valid channel ID or type 'exit' to cancel command.")
            msg = await bot.wait_for('message', check=lambda message: message.author == msg.author)
            await validate_channel(msg, bot)
