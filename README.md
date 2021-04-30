
# Umaru-chan
A general purpose bot made for fun.
## Commands
`.` is the default command prefix. Outside of changing preferences.json, there is not yet a way to change it, though it is planned (i.e. I'm lazy/forgetful).

- `.audit`
	> For configuring the audit feature, which keeps tracks of messages sent on the server. It can be enabled, disabled, and assigned the channel. It is currently unfinished.
- `.greet`
	>`enable, disable, channel, message` <br />
	Configuration for the bot greeting new members. It is disabled by default.
- `.lvl`
	>`@member` (optional) <br />
	Retrieves the member's level. Without mentioning a member, it will default to message author.
- `.ping`
	> pong
- `.roll` 
	> `(x)d(y)` where x = number of dice and y = sides of die. Example: .roll 1d20. <br />
	A simple dice rolling feature.
- `.say`
	> `x` where x is the message <br />
    A simple feature that allows a user to send a message that is then repeated by the bot. The original message is also deleted.
- `.top`
	> `x` where x equals the number of members to be shown. If none  is specified, it defaults to the top 10. <br />
	Retrieves the desired number of members of the highest scores/levels in descending order. 
- `.tz`
	> `x y z` where x = time, y = original timezone, z = desired timezone. HH:MM format required. <br />
	A timezone conversion feature. <br />
	Examples: `14:30 PST GDT` or `09:45PM EST GMT`
