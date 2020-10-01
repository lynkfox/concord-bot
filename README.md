# concord-bot

CONCORD-Bot is a discord bot developed in Python using the discord.py library. It's primary goal is to provide security and utility for Eve Echoes Guilds.

Currently the bot is only good for a single server at a time. I have not set it up for multiple server access.If you want to run it, then you need to host your own version. You can do so following these instructions, but having someone who knows python will be helpful because I'm sure it will need tweaking.

## Necessary Installation

You will need to get a discord authentication token for bots from discord.com/developers

you will need to run

pip install -U discord python-dotenv

a .env file will need to be created with all the environment variables. Excepting the Discord_token all the env variables are ID's (int)

* DISCORD_TOKEN=/your token/
* MOD_CHANNEL=/the id of the channel you want logs of the commands being used goes to/
* ENTRY_EXIT_CHANNEL=/the id of the channel you want join notifications/
* NEWBIE_ROLE=/the id of the role that has extreme limited access/
* VERIFIED_ROLE=/the id of the role that can access the internal areas of your server/
* SECURITY_ROLE=/the id of the role that can approve others to enter the internal areas/
* CHECKPOINT_CAT=/the category id that you want the private rooms to appear under/
* GENERAL_CHAT=/the general chat area you want a welcome message for the new comer to be placed AFTER being verified/

the current !help command is specific to my server. You will want to edit it to be more aligned to yours.

the current 'Welcome to our Server' message is also aligned for mine. You'll want to edit it as well

# Functionality

## On Join Private Channel
When a new user joins the discord they are placed immediately into their own private channel, under the CHECKPOINT_CAT category. They can talk, read, have history, and can upload images.  A message is sent to the ENTRY_EXIT_CHANNEL about them joining. If their account is less than 7 days old there is a warning for SECURITY_ROLE

After the user has been verified by a member of SECURITY ROLE then the security role member can use !verify @name (it has to be the mention). This will delete the channel and add the VERIFIED_ROLE to the new ueser allowing them to see whatever the verified role is set to see.

It will remove the NEWBIE_ROLE as well. It will also put a welcome message in the GENERAL_CHAT

# Forthcoming

(alt commands will require some connection to a database)

!alt main ID (assumes Discord Display Name is main character name)

!alt [add|remove] Name|Number - Name|Number - Name|Number ect

!channelPass - in game channel passwords

!changePass [channelName] [newpass]

