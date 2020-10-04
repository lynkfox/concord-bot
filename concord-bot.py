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
TOKEN = os.getenv('DISCORD_TOKEN')  # Your Discord Bot Token
VERIFIED = int(os.getenv('VERIFIED_ROLE')) # The Role ID that allows access into the server
MODLOG = int(os.getenv('MOD_CHANNEL')) # The ID of the channel that you want the bot to log to
SECURITY = int(os.getenv('SECURITY_ROLE')) # The ID Of the role that can !verify or !reject
CHECKPOINT = int(os.getenv('CHECKPOINT_CAT')) # The ID of the category the private channel should be in
GENERAL = int(os.getenv('GENERAL_CHAT')) # The ID of the general chat for a welcome aboard message
JOINLEAVE = int(os.getenv('ENTRY_EXIT_CHANNEL')) # the ID of the channel where Join/Leave message go
NEWB = int(os.getenv('NEWBIE_ROLE')) # The ID of the role that is auto assigned on join
APPLICANT = int(os.getenv('APPLICANT_ROLE')) # the ID of the role that says they are an applicant
DIPLOMAT = int(os.getenv('DIPLOMAT_ROLE')) # The ID of the role for diplomats.

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
async def on_member_remove(member):
    guild = member.guild
    joinLeaveChannel = guild.get_channel(JOINLEAVE)
    memberRoles = member.roles
    memberRolesListed = ""

    # Remove @everyone from the role list.
    memberRoles.pop(0)

    logger.info(f'ON_MEMBER_REMOVE: {member.name} has left the server.')

    # generate a single string of all the roles as mentionables.
    for role in memberRoles:
        memberRolesListed=memberRolesListed + " " + role.mention

    logEmbed = discord.Embed(title="Member has Left", color=0xB81604)
    logEmbed.description = f'{member.mention} ( {member.name} ) has left the server'
    logEmbed.add_field(name='Roles', value=memberRolesListed)
    logEmbed.set_thumbnail(url=member.avatar_url)

    await joinLeaveChannel.send(embed=logEmbed)
    logger.info(f'ON_MEMBER_REMOVE: Leave Embed pushed to {joinLeaveChannel} channel')


@bot.event
async def on_member_join(member):
    guild = member.guild
    privateChannelName=str(member).replace(' ', '-').replace('#', '-').lower()
    joinLeaveChannel = guild.get_channel(JOINLEAVE)
    newbieRole = guild.get_role(NEWB)
    checkpointCategory = guild.get_channel(CHECKPOINT)
    securityTeam = guild.get_role(SECURITY)


    # log join
    logger.info(f'ON_MEMBER_JOIN: {member.name} has joined the server. Private room of {privateChannelName} created')

    # Give the member the 'Just Joined' role
    await member.add_roles(newbieRole)

    # Set of permissions for the new channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        securityTeam: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                                  read_message_history=True),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                            read_message_history=True)

    }

    privateChannel = await guild.create_text_channel(privateChannelName, overwrites=overwrites,
                                                     category=checkpointCategory)
    # welcome message
    await privateChannel.send(f'{member.mention}, Welcome! You are new to our server! Here is a private channel for us '
                              f'to interview you.')
    await privateChannel.send(f'We take security very seriously here!\n\nOne of our {securityTeam.mention} team members '
                              f'will be along shortly to interview you.\n\nIn the mean time stop by #welcome-to-home '
                              f'in order to choose why you\'ve come to HOME and be allowed to chat in #welcome-lobby. '
                              f'If you are here to Apply to join HOME, you can speed up the process by leaving a '
                              f'screenshot of your character select screen for all of your accounts.\n\nThanks for your'
                              f' patience and welcome to HOME!')

    # Server Entry Exit Logging - create the Embed
    logEmbed = discord.Embed(title="New Member Joined", color=0x00A71E)
    logEmbed.description = f'{member.mention} ( {member.name} ) has joined the server'
    logEmbed.add_field(name='Create Date', value=member.created_at)
    logEmbed.add_field(name='Private Channel', value=privateChannelName)
    logEmbed.set_thumbnail(url=member.avatar_url)

    # check if account less than 7 days old - 604800 seconds is 7 days
    if time.time() - member.created_at.timestamp() < 604800:
        # set log message for file
        logger.info(
            f'ON_MEMBER_JOIN: {member.name} was created on {member.created_at} - which is less than 7 days ago.')

        # mention security role if the account is less than 7 days old
        logEmbed.add_field(name='WARNING', value=f'{securityTeam.mention} this account is less than 7 days old')

    # add the embed to the joinleave channel and add to the log file
    await joinLeaveChannel.send(embed=logEmbed)
    logger.info(f'ON_MEMBER_JOIN: Join Embed pushed to {joinLeaveChannel} channel')


@bot.command(name="verify")
async def verify(ctx, member: discord.Member):
    guild = ctx.guild
    currentChannel = ctx.channel
    author = ctx.author
    privateChannelName=str(member).replace(' ', '-').replace('#', '-').lower()
    modLogChannel = guild.get_channel(MODLOG)
    correctPrivateChannel = get(ctx.guild.text_channels, name=privateChannelName)
    generalChannel = guild.get_channel(GENERAL)
    securityTeam = guild.get_role(SECURITY)
    verifiedRole = guild.get_role(VERIFIED)
    newbieRole = guild.get_role(NEWB)
    applicantRole = guild.get_role(APPLICANT)
    validUseOfCommand = False

    # break the process if they forgot to include an target
    if member is None:
        await currentChannel.send('```Need the @name of the person you are attempting to verify```')
        return

    # determine if this is a valid location to use the command by a valid role
    if securityTeam in author.roles and currentChannel == correctPrivateChannel:
        validUseOfCommand = True

    # Create a Welcome Embed for the General Chat channel
    welcomeEmbed = discord.Embed(title="Welcome!", color=0xBA2100,
                                 description=f'{member.mention} has joined us. Welcome '
                                             f'them to their new HOME.'
                                             f'\n\n{member.display_name} please check '
                                             f'out #role-request to pick your '
                                             f'department(s) and focus.')
    welcomeEmbed.set_thumbnail(url=member.avatar_url)

    # Create a You've Joined, Need to Know info Embed

    newPlayerEmbed1 = discord.Embed(title="Congrats! You've been accepted into HOME", color=0xB81604,
                                    description=f'{member.display_name} here are a few things you should know now that '
                                                f'you\'ve joined HOME \n\n')
    newPlayerEmbed1.add_field(name="Useful Commands", value="Some information for you to know", inline=True)
    newPlayerEmbed1.add_field(name="!commands", value="A list of many commands available between our Bots here.")
    newPlayerEmbed1.add_field(name="!channelPass", value="The in game channel names and most recent passwords.")

    newPlayerEmbed2 = discord.Embed(title="The Golden Horde Charter", color=0xFCC603,
                                    description="The Golden Horde Charter (link is forthcoming)\n\n"
                                                "This is a big document, once its finalized, and it will have all the "
                                                "rules every member Corporation of the Golden Horde Alliance is "
                                                "expected to follow. Please find some time to read through it when you"
                                                "can.")
    newPlayerEmbed3 = discord.Embed(title="Quick And Dirty - Important Charter Rules", color=0xB81604,
                                    description=f'The quick and dirty you should know:\n\n'
                                                f'There are rules to claiming Anoms and Loot. ( Section X.#.#.# )\n\n'
                                                f'There are no claims to mining. We all chew rocks together. '
                                                f'( Section X.#.#.# ) \n\n'
                                                f'DO NOT Kill bases without Express Permission. This is an offense '
                                                f'considered HIGH TREASON. Leadership will decide when to cull a '
                                                f'base\n\n')

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="Verify Command Used:", color=0x00B2FF)

    if validUseOfCommand == True:
        # add Verified and remove Newbie
        await member.add_roles(verifiedRole, reason='Verify Command')
        await member.remove_roles(newbieRole)
        await member.remove_roles(applicantRole)
        logEmbed.description = f'{ctx.author.mention} verified {member.mention}'

        # Send the Welcome and New Associate Embeds
        await generalChannel.send(embed=welcomeEmbed)
        await member.send(embed=newPlayerEmbed1)
        await member.send("https://discord.gg/3XqEYZfhttps://discord.gg/3XqEYZf")
        await member.send(embed=newPlayerEmbed2)
        await member.send(embed=newPlayerEmbed3)

        # log the channel about to be deleted
        logger.info(f'VERIFY: Deleted Channel {currentChannel}')
        await currentChannel.send(':white_check_mark:')
        await currentChannel.send('Deleting this channel in 15 seconds.')

        # wait 15 seconds then delete the channel
        await asyncio.sleep(15)
        await currentChannel.delete()
    else:
        logEmbed.description = f'{ctx.author.mention} tried to use !verify on {member.mention} in {currentChannel}.\n\n' \
                               f'They either do not have the proper permissions or it was an invalid channel'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)
        logger.info(f'VERIFY: {securityTeam} role not found or {currentChannel} is not valid!')

    await modLogChannel.send(embed=logEmbed)

@bot.command(name="reject")
async def reject(ctx, member: discord.Member):
    guild = ctx.guild
    currentChannel = ctx.channel
    author = ctx.author
    privateChannelName=str(member).replace(' ', '-').replace('#', '-').lower()
    joinLeaveChannel = guild.get_channel(JOINLEAVE)
    modLogChannel = guild.get_channel(MODLOG)
    correctPrivateChannel = get(ctx.guild.text_channels, name=privateChannelName)
    securityTeam = guild.get_role(SECURITY)
    validUseOfCommand = False

    # break the process if they forgot to include an target
    if member is None:
        await currentChannel.send('```Need the @name of the person you are attempting to verify```')
        return

    # determine if this is a valid location to use the command by a valid role
    if securityTeam in author.roles and currentChannel == correctPrivateChannel:
        validUseOfCommand = True

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="Reject Command Used;", color=0xBA2100)

    if validUseOfCommand == True:

        # DM the member
        await member.send("Thank\'s for your interest in HOME. Either you or we decided this wasn\'t the place to "
                          "rest your head (or you didn\'t respond to inquiries for the interview process). "
                          "No hard feelings! Perhaps you\'ll find your HOME elsewhere!")

        # Logging
        logger.info(f'REJECT: Deleted Channel {currentChannel}, DM sent to {member}')
        logEmbed.description = f'{ctx.author.mention} rejected {member.mention}. They will be kicked from the server ' \
                               f'in 15 seconds.'

        await currentChannel.send(':x:')
        await currentChannel.send('Deleting this channel in 15 seconds.')

        # wait 15 seconds then delete the channel
        await asyncio.sleep(15)
        await currentChannel.delete()
        await guild.kick(member, reason=f"Reject Command Used by {author.name}")

    else:
        logEmbed.description = f'{ctx.author.mention} tried to use !reject on {member.mention} in {currentChannel}.\n\n' \
                               f'They either do not have the proper permissions or it was an invalid channel'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)
        logger.info(f'reject: {securityTeam} role not found or {currentChannel} is not valid!')

    await modLogChannel.send(embed=logEmbed)


@bot.command(aliases=['bot', 'commands', 'fuckingbot', 'help'])
async def command(ctx):
    author = ctx.author
    guild = ctx.guild

    helpEmbed = discord.Embed(title="CONCORD Bot Help", color=0xFFFFFF)
    helpEmbed.set_thumbnail(url=guild.icon_url)
    helpEmbed.description = 'These are the Following Commands that you can use on HOME at the Associate level'
    helpEmbed.add_field(name="!command | !commands", value='This command')
    helpEmbed.add_field(name="!industry | !military",
                        value='Links to the Spreadsheets where we keep track of our members skills')
    helpEmbed.add_field(name="!buyback", value='Link to the Spreadsheet that contains the Ore Buyback Form')
    helpEmbed.add_field(name="!buildcalc",
                        value='Link to Lynk\'s Build Calculator for determining how much you need to mine')
    helpEmbed.add_field(name="!corp", value="Get the in Game Corp business cards to help searching for them")

    if ctx.guild.get_role(int(VERIFIED)) not in author.roles:
        return
    else:
        await ctx.channel.send(f'Bot Commands are on their way to your DM\'s {author.mention}')
        await author.send(embed=helpEmbed)
        logger.info(f'HELP: {author.name} used the help command')


@bot.command(aliases=["recruiter", "recruit", "rHelp", "rhelp", "security", "verifyhelp"])
async def recuiter(ctx):
    author = ctx.author
    guild = ctx.guild

    helpEmbed = discord.Embed(title="CONCORD Bot Recruiter Help", color=0xFFFFFF)
    helpEmbed.set_thumbnail(url=guild.icon_url)
    helpEmbed.description = 'These are the Following Commands that you can use on HOME at the Recruiter level'
    helpEmbed.add_field(name="!recruiter | !recruit | !rHelp", value='This command')
    helpEmbed.add_field(name="!verify @name",
                        value='Only usable in the private channels auto generated by the bot on a new user join. '
                              'It will remove the Applicant and Just Joined! roles and assign Associate. It will'
                              'send a welcome message to the general chat and a useful new rules DM to the one '
                              'mentioned. It will delete the room in 15 seconds. If done correctly you will see'
                              'CONCORD-Bot respond with :white-check-mark:', inline=False)
    helpEmbed.add_field(name="!reject @name",
                        value='Only usable in the private channels auto generated by the bot on a new user join. '
                              'It will remove the channel and kick the user mentioned after 15 seconds. It will '
                              'send a DM to the user kicked explaining what happened.', inline=False)

    if ctx.guild.get_role(int(SECURITY)) not in author.roles:
        return
    else:
        await ctx.channel.send(f'Recruiter commands on their way to your DM\'s {author.mention}')
        await author.send(embed=helpEmbed)
        logger.info(f'HELP: {author.name} used the recruiter help command')


@bot.command(name='Skynet')
async def command(ctx, message):
    author = ctx.author
    generalchat = get(ctx.guild.text_channels, id=GENERAL)

    if author.id == int(182249916087664640):
        await generalchat.send(message)


@bot.command(name='corp')
async def corp(ctx):
    author = ctx.author
    channel = ctx.channel

    cardEmbed = discord.Embed(title="In Game Corp", description="How to find HOME in game.")
    cardEmbed.add_field(name="HOME - Up to 2 clones per player (subject to change)",
                        value=" Search for HOME or 1000000581", inline=False)
    cardEmbed.add_field(name="HOM2 - All your other Alts",
                        value=" Search for HOM2 or 1000008117", inline=False)
    cardEmbed.set_image(url="https://cdn.discordapp.com/attachments/743284961225998406/762367195334049882/unknown.png")

    await channel.send(embed=cardEmbed)
    logger.info(f'CORP: {author.name} used the corp buisness card command in #{channel}')

'''
@bot.command(name="test")
async def command(ctx):
    memberRolesListed=""
    roles = ctx.author.roles

    roles.pop(0)

    for role in roles:
        memberRolesListed=memberRolesListed + " " + role.mention

    await ctx.channel.send(memberRolesListed)
'''

bot.run(TOKEN)
