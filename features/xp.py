import datetime


async def xp_process(ctx, xp, bot):
    # XP calculations
    # It checks if the message's author has been added
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp["servers"]), None)
    if server is None:
        add_xp_server(ctx, xp, bot)
        # xp['servers'].append(add_server(ctx, xp, bot))
        server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp["servers"]), None)
    user = next(filter(lambda x: x["userId"] == ctx.author.id, server["users"]), None)
    # If the author already exists, it will add the experience.
    if user is not None:
        user.update(await add(ctx, user))
    # If the author doesn't exist in the list, it will add them to xp json along with the experience
    elif user is None:
        print("Adding {} to the Leaderboard".format(ctx.author))
        server['users'].append(await populate_exist(ctx))
    # If the server hasn't been added, it will then add it along with the author and experience.
    return xp


async def add(msg, user):
    new_xp = user['userTotalXp'] + msg_length(msg.content)
    last_msg = datetime.datetime.strptime(user['lastMsg'], '%Y-%m-%dT%H:%M:%S.%f')
    if (msg.created_at - last_msg).total_seconds() >= 120.0:
        lvl = check_level(new_xp, user['userLvl'])
        if lvl > user['userLvl']:
            await msg.channel.send("Congrats! {} has leveled up to level {}!".format(msg.author.mention, lvl))
            return {"userTotalXp": new_xp, "lastMsg": msg.created_at.isoformat(), "userLvl": lvl,
                    "nextLvl": next_lvl(lvl)}
        else:
            return {"userTotalXp": new_xp, "lastMsg": msg.created_at.isoformat()}
    return user


async def populate_exist(msg):
    xp = msg_length(msg.content)
    lvl = check_level(xp, 1)
    if lvl > 1:
        await msg.channel.send("Congrats! {} has leveled up to level {}!".format(msg.author.mention, lvl))
    return {
        "userId": msg.author.id,
        "userTotalXp": msg_length(msg.content),
        "userLvl": lvl,
        "nextLvl": next_lvl(lvl),
        "lastMsg": msg.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f'),
        "server": msg.guild.id
    }


def populate_new(mem, xp, bot):
    now = datetime.datetime.now()
    # XP calculations
    # It checks if the message's author has been added
    server = next(filter(lambda x: x["serverId"] == mem.id, xp["servers"]), None)
    if server is None:
        xp['servers'].append(add_xp_server(mem, xp, bot))
        server = next(filter(lambda x: x["serverId"] == mem.author.id, xp["servers"]), None)
    user = next(filter(lambda x: x["userId"] == mem.id, server["users"]), None)
    # If the author already exists, it will return.
    if user is not None:
        return
    # If the author doesn't exist in the list, it will add them to xp json
    elif user is None:
        print("Adding {} to the Leaderboard".format(user))
        xp['users'].append({
            "userId": mem.id,
            "userTotalXp": 0,
            "userLvl": 1,
            "nextLvl": next_lvl(1),
            "lastMsg": now.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "server": mem.guild.id
        })
    return xp


def check_level(current_xp, lvl):
    if current_xp >= next_lvl(lvl):
        return check_level(current_xp, (lvl + 1))
    else:
        return lvl


def msg_length(content):
    if len(content) >= 500:
        return 500
    else:
        return len(content)


def next_lvl(lvl):
    lvl += 1
    return round((4 * (lvl * lvl * lvl)) / 5)


def add_xp_server(ctx, file, bot):
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
    return

