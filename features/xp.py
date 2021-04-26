import datetime


async def xp_process(ctx, xp):
    # XP calculations
    server = next(filter(lambda x: x["serverId"] == ctx.guild.id, xp["servers"]), None)
    # Checks the xp.json file to see if the server has been added
    if server is not None:
        # It then checks if the message's author has been added
        user = next(filter(lambda x: x["userId"] == ctx.author.id, server["users"]), None)
        # If the author already exists, it will add the experience.
        if user is not None:
            user.update(await add(ctx, user))
        # If the author doesn't exist in the list, it will add them to xp.json along with the experience
        elif user is None:
            print("Adding {} to the Leaderboard".format(ctx.author))
            server['users'].append(await populate_exist(ctx))
    # If the server hasn't been added, it will then add it along with the author and experience.
    elif server is None:
        xp['servers'].append({"serverId": ctx.guild.id, "users": []})
        xp = await xp_process(ctx, xp)
    # write_to_json(xp, xp['path'])
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
        "lastMsg": msg.created_at.isoformat(),
        "server": msg.guild.id
    }


def populate_new(mem, xp):
    # XP calculations
    server = next(filter(lambda x: x["serverId"] == mem.guild.id, xp["servers"]), None)
    # Checks the xp.json file to see if the server has been added
    if server is not None:
        # It then checks if the message's author has been added
        user = next(filter(lambda x: x["userId"] == mem.id, server["users"]), None)
        # If the author already exists, it will return.
        if user is not None:
            return
        # If the author doesn't exist in the list, it will add them to xp.json
        elif user is None:
            print("Adding {} to the Leaderboard".format(user))
            server['users'].append({
                "userId": mem.id,
                "userTotalXp": 0,
                "userLvl": 1,
                "nextLvl": next_lvl(1),
                "lastMsg": "2021-01-01T00:00:00.000000",
                "server": mem.guild.id
            })
    # If the server hasn't been added, it will then add it along with the author.
    elif server is None:
        xp['servers'].append({"serverId": mem.guild.id, "users": []})
        populate_new(mem, xp)
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
