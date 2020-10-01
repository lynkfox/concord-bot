import os
import logging
import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import time

# Env Variables for security
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VERIFIED = int(os.getenv('VERIFIED_ROLE'))
MODLOG = int(os.getenv('MOD_CHANNEL'))
SECURITY = int(os.getenv('SECURITY_ROLE'))
CHECKPOINT = int(os.getenv('CHECKPOINT_CAT'))
GENERAL = int(os.getenv('GENERAL_CHAT'))
JOINLEAVE = int(os.getenv('ENTRY_EXIT_CHANNEL'))
NEWB = int(os.getenv('NEWBIE_ROLE'))

# logger setup
logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# set the command prefix to bang
bot = commands.Bot(command_prefix='!')

# remove the default help command
bot.remove_command('help')




@bot.event
async def on_ready():
    logger.info(f'ON_READY: {bot.user} has logged in.')


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
    tempName = str(member).replace(' ', '-').replace('#', '').lower()
    mention = member.mention
    securityRole = guild.get_role(int(SECURITY))

    # log join
    logger.info(f'ON_MEMBER_JOIN: {member.name} has joined the server.')

    # Set of permissions for the new channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        securityRole: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                                  read_message_history=True),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                            read_message_history=True)

    }
    tempChannel = await guild.create_text_channel(tempName, overwrites=overwrites)

    # Get the category for the checkpoint
    for category in guild.categories:
        if category.id == CHECKPOINT:
            await tempChannel.edit(category=category)
            # log channel creation
            logger.info(f'ON_MEMBER_JOIN: Channel Created {tempChannel} under {category}')

    # welcome message
    await tempChannel.send(f'{mention}, Welcome! You are new to our server! Here is a private channel for us to '
                           'interview you.')
    await tempChannel.send(f'We take security very seriously here!\n\nOne of our {securityRole.mention} Staff will be '
                           'along to aid you soon. In the meantime, check out the #welcome-to-home channel and select '
                           'your reason for being here. Then you can chat in the #welcome-lobby\n\nIf You are applying '
                           'to HOME, you can speed up the process by posting an in game screenshot of your entire '
                           'character sheet. Thanks!')

    # Server Entry Exit Logging - create the Embed

    logEmbed = discord.Embed(title="New Member Joined", color=0x00A71E)
    logEmbed.description = f'{member.mention} ( {member.name} ) has joined the server'
    logEmbed.add_field(name='Create Date', value=member.created_at)
    logEmbed.add_field(name='Private Channel', value=tempName)
    logEmbed.set_thumbnail(url=member.avatar_url)

    # check if account less than 7 days old - 604800 seconds is 7 days
    if time.time() - member.created_at.timestamp() < 604800:

        # set log message for file
        logger.info(f'ON_MEMBER_JOIN: {member.name} was created on {member.created_at} - which is less than 7 days ago.')

        # mention security role if the account is less than 7 days old
        securityRole = guild.get_role(int(SECURITY))
        logEmbed.add_field(name='WARNING', value=f'{securityRole.mention} this account is less than 7 days old')

    # add the embed to the joinleave channel and add to the log file
    await guild.get_channel(JOINLEAVE).send(embed=logEmbed)
    logger.info(f'ON_MEMBER_JOIN: Join Embed pushed to {JOINLEAVE} channel')

@bot.command(name='verify')
async def verify(ctx, member: discord.Member):
    channel = ctx.channel
    verifiedRole = ctx.guild.get_role(VERIFIED)
    newbieRole = ctx.guild.get_role(NEWB)
    logger.info('VERIFY: {0.display_name} used verify on {1.name}'.format(ctx.author, member))
    tempName = str(member).replace(' ', '-').replace('#', '').lower()
    securityRole = ctx.guild.get_role(int(SECURITY))
    allowed = False
    correctChannel = get(ctx.guild.text_channels, name=tempName)
    generalchat = get(ctx.guild.text_channels, id=GENERAL)

    # Create a Welcome Embed for the General Chat channel
    welcomeEmbed = discord.Embed(title="Welcome!", color=0xBA2100,
                                 description=f'{member.mention} has joined us. Welcome '
                                             f'them to their new HOME.'
                                             f'\n\n{member.display_name} please check '
                                             f'out #role-request to pick your '
                                             f'department(s) and focus.')
    welcomeEmbed.set_thumbnail(url=member.avatar_url)

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="Verify Command", color=0xBA2100)

    # break the process if they forgot to include an target
    if member is None:
        await channel.send('```Need the @name of the person you are attempting to verify```')
        return

    # Check to make sure the author has the SECURITY_ROLE and is using it in the private channel that the @mention
    # indicates
    if securityRole in ctx.author.roles and ctx.channel == correctChannel:

        # add Verified and remove Newbie
        await member.add_roles(verifiedRole, reason='Verify Command')
        await member.remove_roles(newbieRole)
        logEmbed.description = f'{ctx.author.mention} verified {member.mention}'

        # Send the Embeds
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)
        await generalchat.send(embed=welcomeEmbed)

        # log the channel about to be deleted
        logger.info('VERIFY: Deleted Channel {0.name}'.format(channel))
        await channel.send(':white_check_mark:')
        await channel.send('Deleting this channel in 15 seconds.')

        # wait 15 seconds then delete the channel
        await asyncio.sleep(15)
        await channel.delete()

    # if they don't have the Security role, log that.
    elif securityRole not in ctx.author.roles:
        logEmbed.description = f'{ctx.author.mention} tried to use !verify on {member.mention} but they do not have ' \
                               f'the {securityRole.name} role'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)
        logger.info(
            f'VERIFY: {ctx.author.display_name} failed to use command on {member.name} because they don\'t have '
            f'the {securityRole.name} role')

    # if its used in the wrong channel, log that.
    elif ctx.channel.name is not tempName:
        logEmbed.description = f'{ctx.author.mention} tried to use !verify on {member.mention} in channel ' \
                               f'#{ctx.channel.name} and this is not an approved channel.'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)

        logger.info(f'VERIFY: {ctx.author.display_name} failed to use command on {member.name} in an inappropriate'
                    f' channel, {ctx.channel.name}')


# @verify.error
# async def verify_error(ctx, error):
#   if isinstance(error, commands.BadArgument):
#        await ctx.send('I could not find that member... (be sure to use @Name and use the quick mention!)')

@bot.command(aliases=['bot', 'commands', 'fuckingbot', 'help'])
async def command(ctx):
    author = ctx.author
    guild = ctx.guild

    helpEmbed = discord.Embed(title="CONCORD Bot Help", color=0xFFFFFF)
    helpEmbed.set_thumbnail(url=guild.icon_url)
    helpEmbed.description = 'These are the Following Commands that you can use on HOME at the Associate leve'
    helpEmbed.add_field(name="!command | !commands", value='This command')
    helpEmbed.add_field(name="!industry | !military",
                        value='Links to the Spreadsheets where we keep track of our members skills')
    helpEmbed.add_field(name="!buyback", value='Link to the Spreadsheet that contains the Ore Buyback Form')
    helpEmbed.add_field(name="!buildcalc",
                        value='Link to Lynk\'s Build Calculator for determining how much you need to mine')

    if ctx.guild.get_role(int(VERIFIED)) not in author.roles:
        return
    else:
        await ctx.channel.send(f'Bot Commands are on their way to your DM\'s {author.mention}')
        await author.send(embed=helpEmbed)


@bot.command(name='Skynet')
async def command(ctx, message):
    author = ctx.author
    generalchat = get(ctx.guild.text_channels, id=GENERAL)

    if author.id == int(182249916087664640):
        await generalchat.send(message)


# Command for Alts - not ready yet.
"""
@bot.command(name='alt')
async def alt(ctx, message):

    _command = "Not"
    mainName = ctx.author.display_name
    mainID = 0
    alts = []

    fullSplits = message.Split(">")

    if fullSplits is None or fullSplits.len() <= 1:
        print('Alts command did not have enough arguments')
        return

    if 'add' in fullSplits[0].lower():
        print('Adding Alts')
        _command = "add"
        return

    elif 'remove' in fullSplits[0].lower():
        print('Removing Alts')
        _command = "remove"
        return
    else:
        ctx.channel.send("```!alt [add|remove] - missing command type.```")

    IDOfMain = fullSplits[0].Split()

    if mainID is None or mainID.len() <= 1:
        # Doesn't have id #
        return
    elif mainID[-1].isnumeric():
        # store main ID
        mainID = mainID[-1]
        fullSplits.remove(0)

    for altInfo in fullSplits:
        nameAndID = altInfo.Split()
        altID
        index#
        for word in nameAndID:
            # find the ID #
            if word.isnumeric():
                altID = word





@bot.command(name='test')
async def test(ctx, member: discord.Member):
    welcomeEmbed = discord.Embed(title="Welcome!", color=0xBA2100, )
    welcomeEmbed.set_thumbnail(url=member.avatar_url)
    welcomeEmbed.description = f'{ctx.author.display_name} tried to use !verify on {member.name} but they do not have ' \
                               f'the  role'

    await ctx.channel.send(embed=welcomeEmbed)
"""

bot.run(TOKEN)
