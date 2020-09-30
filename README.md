# concord-bot

CONCORD-Bot is a discord bot developed in Python using the discord.py library. It's primary goal is to provide security and utility for Eve Echoes Guilds.

## Necessary Installation
a .env file will need to be created with all the environment variables. Excepting the Discord_token all the env variables are ID's (int)

* DISCORD_TOKEN
* MOD_CHANNEL
* VERIFIED_ROLE
* SECURITY_ROLE
* CHECKPOINT_CAT

# Functionality

## On Join Private Channel
When a new user joins the discord they are placed immediately into their own private channel, under the CHECKPOINT_CAT category. They can talk, read, have history, and can upload images. 

After the user has been verified by a member of SECURITY ROLE then the security role member can use !verify @name (it has to be the mention). This will delete the channel and add the VERIFIED_ROLE to the new ueser allowing them to see what wever the verified role is set to see.
