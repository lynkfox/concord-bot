import os
import logging
import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VERIFIED = int(os.getenv('VERIFIED_ROLE'))
MODLOG = int(os.getenv('MOD_CHANNEL'))

bot = commands.Bot(command_prefix='!')
logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


@bot.event
async def on_member_join(member):
    guild = member.guild
    tempName = str(member)

    # Set of permissions for the new channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, read_message_history=True)

    }
    tempChannel = await guild.create_text_channel(tempName, overwrites=overwrites, category="Lobby")
## TO DO - Remove Hard coded role id
    await tempChannel.send('${member}, Welcome! You are new to our server! Here is a private channel for us to interview you.')
    await tempChannel.send('We take security very seriously here!\n\nOne of our <@&756849372402024569> Staff will be along to aid you soon. In the meantime, check out the #welcome-to-home channel and select your reason for being here. Then you can chat in the #welcome-lobby\n\nIf You are applying to HOME, you can speed up the process by posting an in game screenshot of your entire character sheet. Thanks!')


@bot.command(name='verify')
async def verify(ctx, member: discord.Member):
    channel = ctx.channel
    verifiedRole = ctx.guild.get_role(VERIFIED)
    logStatement = '{0.name} verified {1.name}'.format(ctx.author, member)
    logger.info('VERIFY: {0.name} verified {1.name}'.format(ctx.author, member))

    await member.add_roles(verifiedRole, reason=logStatement)
    await ctx.guild.get_channel(MODLOG).send(logStatement)
    await channel.send(':white_check_mark:')
    await channel.send('Deleting this channel in 15 seconds.')
    await asyncio.sleep(15)
    logger.info('VERIFY: Deleted Channel {0.name}'.format(channel))
    await channel.delete()


#@verify.error
#async def verify_error(ctx, error):
#   if isinstance(error, commands.BadArgument):
#        await ctx.send('I could not find that member... (be sure to use @Name and use the quick mention!)')


@bot.command(name='test')
async def test(ctx):
    print('test')
    channel = ctx.channel
    print(VERIFIED)
    print(MODLOG)
    verifiedRole = ctx.guild.get_role(int(VERIFIED))
    print(channel)
    print(verifiedRole)

bot.run(TOKEN)
