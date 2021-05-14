
# Umaru-chan
A general purpose bot made for fun.
## Commands
`.` is the default command prefix. Outside of changing preferences.json, there is not yet a way to change it, though it is planned (i.e. I'm lazy/forgetful).

- `.birthday`
    > Allows users to enter their birthday (MM/DD) and the time the bot will remind them. Users can also change or remove their birthday. Users can only edit their own.
- `.lvl`
	>`@member` (optional) <br />
	Retrieves the member's level. Without mentioning a member, it will default to message author.
- `.ping`
	> pong
- `.roll` 
	> `(x)d(y)` where x = number of dice and y = sides of die. <br />
	A simple dice rolling feature.<br />
    Example: `.roll 1d20.` 
- `.say`
	> `x` where x is the message <br />
    A simple feature that allows a user to send a message that is then repeated by the bot. The original message is also deleted.
- `.setup`
	>`audit greet xp birthday audit prefix` <br />
	Command for setting up or changing the different features. Only usable by Administrators. `audit` and `prefix` are currently disabled/unfinished.
- `.top`
	> `x` where x equals the number of members to be shown. If none  is specified, it defaults to the top 10. <br />
	Retrieves the desired number of members of the highest scores/levels in descending order. 
- `.tz`
	> `x y z` where x = time, y = original timezone, z = desired timezone. HH:MM format required. <br />
	A timezone conversion feature. <br />
	Examples: `14:30 PST GDT` or `09:45PM EST GMT`
