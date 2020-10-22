import os
import logging
import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import time
from datetime import datetime

# Env Variables for security
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # Your Discord Bot Token
VERIFIED = int(os.getenv('VERIFIED_ROLE')) # The Role ID that allows access into the server
MODLOG = int(os.getenv('MOD_CHANNEL')) # The ID of the channel that you want the bot to log to
DONATION = int(os.getenv('DONATION_CHANNEL'))
ERROR = int(os.getenv('ERROR_CHANNEL'))
SECURITY = int(os.getenv('SECURITY_ROLE')) # The ID Of the role that can !verify or !reject
CHECKPOINT = int(os.getenv('CHECKPOINT_CAT')) # The ID of the category the private channel should be in
GENERAL = int(os.getenv('GENERAL_CHAT')) # The ID of the general chat for a welcome aboard message
JOINLEAVE = int(os.getenv('ENTRY_EXIT_CHANNEL')) # the ID of the channel where Join/Leave message go
NEWB = int(os.getenv('NEWBIE_ROLE')) # The ID of the role that is auto assigned on join
APPLICANT = int(os.getenv('APPLICANT_ROLE')) # the ID of the role that says they are an applicant
DIPLOMAT = int(os.getenv('DIPLOMAT_ROLE')) # The ID of the role for diplomats.
KICK = int(os.getenv('KICK_ROLE')) # The ID of the role that can use the Kick Command
COMBAT = int(os.getenv('COMBAT_ROLE')) # ID of the special combat role
MINING = int(os.getenv('MINING_ROLE')) # ID of the special miner role
CHIEFSECURITY = int(os.getenv('COS_ROLE'))
MININGDIRECTOR = int(os.getenv('DOM_ROLE'))
INDUSTRYDIRECTOR = int(os.getenv('DOI_ROLE'))
FINANCEDIRECTOR = int(os.getenv('DOF_ROLE'))
CEO = int(os.getenv('CEO_ROLE'))
ADVISORYBOARD = int(os.getenv('ADVISORY_ROLE'))


TitleDict = {
    "Chief of Security" : "[CoS]",
    "Director of Mining" : "[DoM]",
    "Director of Industry" : "[DoI]",
    "Director of Finance" : "[DoF]",
    "CEO" : "CEO",
    "Advisory Board" : "[AB]"
}

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
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    logger.info(f'({current_time}) ON_READY: {bot.user} has logged in.')

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

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")

    # Remove @everyone from the role list.
    memberRoles.pop(0)

    logger.info(f'({current_time}) ON_MEMBER_REMOVE: {member.name} has left the server.')

    # generate a single string of all the roles as mentionables.
    for role in memberRoles:
        memberRolesListed=memberRolesListed + " " + role.mention

    logEmbed = discord.Embed(title="Member has Left", color=0xB81604)
    logEmbed.description = f'{member.mention} ( {member.name} ) has left the server'
    logEmbed.add_field(name='Roles', value=memberRolesListed)
    logEmbed.set_thumbnail(url=member.avatar_url)

    # check to see if the user had a private discord channel still
    privateChannelName = str(member).replace(' ', '-').replace('#', '-').lower()

    if privateChannelName in guild.channels:
        logEmbed.add_field(name="Private Channel:", value=f"User still had a Private channel, {privateChannelName}. "
                                                          f"An attempt to delete it will happen in 30 seconds.")

    await joinLeaveChannel.send(embed=logEmbed)
    logger.info(f'ON_MEMBER_REMOVE: Leave Embed pushed to {joinLeaveChannel} channel')

    await asyncio.sleep(30)
    try:
        await guild.get_channel(name=privateChannelName).delete()
        logger.info(f'ON_MEMBER_REMOVE: {privateChannelName} successfully deleted')
    except:
        pass

@bot.event
async def on_member_join(member):
    guild = member.guild
    privateChannelName=str(member).replace(' ', '-').replace('#', '-').lower()
    joinLeaveChannel = guild.get_channel(JOINLEAVE)
    newbieRole = guild.get_role(NEWB)
    checkpointCategory = guild.get_channel(CHECKPOINT)
    securityTeam = guild.get_role(SECURITY)
    justJoinedNick = "("+str(member.display_name)+")"

    await member.edit(nick=justJoinedNick)

    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

    # log join
    logger.info(f'({current_time}) ON_MEMBER_JOIN: {member.name} has joined the server. Private room of {privateChannelName} created')

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

    await joinLeaveChannel.send(embed=logEmbed)
    logger.info(f'ON_MEMBER_JOIN: Join Embed pushed to {joinLeaveChannel} channel')
    # check if account less than 7 days old - 604800 seconds is 7 days
    if time.time() - member.created_at.timestamp() < 604800:
        # set log message for file
        logger.info(
            f'ON_MEMBER_JOIN: {member.name} was created on {member.created_at} - which is less than 7 days ago.')

        # mention security role if the account is less than 7 days old
        await joinLeaveChannel.send(f'{securityTeam.mention} the above account is less than 7 days old')


@bot.command(name="verify")
async def verify(ctx, member: discord.Member):
    guild = ctx.guild
    currentChannel = ctx.channel
    author = ctx.author
    baseNick = str(member).split("#")[0]
    memberNumber = str(member).split("#")[1]
    sanitizedName = str(member.display_name)[1:-1].replace(' ', '-').replace('#', '-').replace('[','').replace(']','').lower()
    privateChannelName = sanitizedName+"-"+memberNumber
    modLogChannel = guild.get_channel(MODLOG)
    correctPrivateChannel = get(ctx.guild.text_channels, name=privateChannelName)
    generalChannel = guild.get_channel(GENERAL)
    securityTeam = guild.get_role(SECURITY)
    verifiedRole = guild.get_role(VERIFIED)
    newbieRole = guild.get_role(NEWB)
    applicantRole = guild.get_role(APPLICANT)
    validUseOfCommand = False

    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

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
                                    description="The Golden Horde Charter\n\n"
                                                "This is a big document, once its finalized, and it will have all the "
                                                "rules every member Corporation of the Golden Horde Alliance is "
                                                "expected to follow. Please find some time to read through it when you"
                                                "can.")
    newPlayerEmbed2.url = 'https://docs.google.com/document/d/1i9lm7Nvie0DMFZDerfkYAq6ZzLN_4tXS9BxjlPZUmi0/edit?usp=sharing'
    newPlayerEmbed3 = discord.Embed(title="Quick And Dirty - Important Charter Rules", color=0xB81604,
                                    description=f'The quick and dirty you should know:\n\n'
                                                f'There are rules to claiming Anoms and Loot. ( Title 8 )\n\n'
                                                f'There are no claims to mining. We all chew rocks together. '
                                                f'( Title 9) \n\n'
                                                f'DO NOT Kill bases without Express Permission. This is an offense '
                                                f'considered HIGH TREASON. Leadership will decide when to cull a '
                                                f'base\n\n')
    newPlayerEmbed3.add_field(name='Finally, your nick',value="We restrict name changes here for a few reasons, but"
                                                              "only slightly. Just use !nick newnick to change your "
                                                              "display name to match your in game main characters name!")

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="Verify Command Used:", color=0x00B2FF)

    if validUseOfCommand == True:
        # add Verified and remove Newbie
        await member.add_roles(verifiedRole, reason='Verify Command')
        await member.remove_roles(newbieRole)
        await member.remove_roles(applicantRole)
        logEmbed.description = f'{ctx.author.mention} verified {member.mention} | {member.display_name}'

        # Send the Welcome and New Associate Embeds
        await generalChannel.send(embed=welcomeEmbed)
        await member.send(embed=newPlayerEmbed1)
        await member.send("The Golden Horde Discord:\n\nhttps://discord.gg/3XqEYZfhttps://discord.gg/3XqEYZf")
        await member.send(embed=newPlayerEmbed2)
        await member.send(embed=newPlayerEmbed3)

        # log the channel about to be deleted
        logger.info(f'({current_time}) VERIFY: Deleted Channel {currentChannel}')
        await currentChannel.send(':white_check_mark:')
        await currentChannel.send('Deleting this channel in 15 seconds.')
        await member.edit(nick=baseNick)

        # wait 15 seconds then delete the channel
        await asyncio.sleep(15)
        await currentChannel.delete()
    else:
        logEmbed.description = f'{ctx.author.mention} tried to use !verify on {member.mention} | {member.display_name} ' \
                               f'in {currentChannel}.\n\n' \
                               f'They either do not have the proper permissions or it was an invalid channel'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)
        logger.info(f'VERIFY: {securityTeam} role not found or {currentChannel} is not valid!')

    await modLogChannel.send(embed=logEmbed)

@verify.error
async def verify_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    if isinstance(error, commands.BadArgument):
        logger.info(f'({current_time}) VERIFY: Bad Argument')

    else:
        await error_channel.send(f'`VERIFY: Error: {error}`')
        logger.info(f'({current_time}) VERIFY: {error}')



@bot.command(name="reject")
async def reject(ctx, member: discord.Member = None):

    guild = ctx.guild
    currentChannel = ctx.channel
    author = ctx.author
    privateChannelName=str(member).replace(' ', '-').replace('#', '-').lower()
    joinLeaveChannel = guild.get_channel(JOINLEAVE)
    modLogChannel = guild.get_channel(MODLOG)
    correctPrivateChannel = get(ctx.guild.text_channels, name=privateChannelName)
    securityTeam = guild.get_role(SECURITY)
    validUseOfCommand = False

    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

    # break the process if they forgot to include an target
    if member is None:
        await currentChannel.send('```Need the @name of the person you are attempting to verify```')
        return

    # determine if this is a valid location to use the command by a valid role
    if securityTeam in author.roles and currentChannel == correctPrivateChannel:
        validUseOfCommand = True

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="Reject Command Used:", color=0xBA2100)

    if validUseOfCommand == True:

        # Delete the command usage
        await ctx.message.delete(delay=2)

        # DM the member
        await member.send("Thank\'s for your interest in HOME. Either you or we decided this wasn\'t the place to "
                          "rest your head (or you didn\'t respond to inquiries for the interview process). "
                          "No hard feelings! Perhaps you\'ll find your HOME elsewhere!")

        # Logging
        logger.info(f'({current_time}) REJECT: Deleted Channel {currentChannel}, DM sent to {member}')
        logEmbed.description = f'{ctx.author.mention} rejected {member.display_name}. They will be kicked from the ' \
                               f'server in 15 seconds.'

        await currentChannel.send(':wave:')
        await currentChannel.send('Deleting this channel in 15 seconds.')

        # wait 15 seconds then delete the channel
        await asyncio.sleep(15)
        await currentChannel.delete()
        await guild.kick(member, reason=f"Reject Command Used by {author.name}")

    else:
        logEmbed.description = f'{ctx.author.mention} tried to use !reject on {member.display_name} in {currentChannel}.\n\n' \
                               f'They either do not have the proper permissions or it was an invalid channel'
        logger.info(f'({current_time}) REJECT: {securityTeam} role not found or {currentChannel} is not valid!')

    await modLogChannel.send(embed=logEmbed)


@reject.error
async def reject_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    if isinstance(error, commands.BadArgument):
        logger.info(f'({current_time}) REJECT: The targeted member for !reject has aleady left the server or is not'
                    f'a viable target')
        await ctx.channel.send('`The User specified has already left the server, please use the !close command`')
    else:
        await error_channel.send(f'`REJECT: Error: {error}`')
        logger.info(f'({current_time}) REJECT: {error}')


@bot.command(name="close")
async def close(ctx, channel: str = None):
    guild = ctx.guild
    currentChannel = ctx.channel
    author = ctx.author
    modLogChannel = guild.get_channel(MODLOG)
    correctPrivateChannel = get(ctx.guild.text_channels, mention=channel)
    securityTeam = guild.get_role(SECURITY)
    validUseOfCommand = False
    checkpointCategory = guild.get_channel(CHECKPOINT)
    inCategory = False



    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

    for category in guild.by_category():
        if category[0] is checkpointCategory:
            if currentChannel in category[1]:
                inCategory=True

    if securityTeam in author.roles and currentChannel == correctPrivateChannel and inCategory:
        validUseOfCommand = True

    logEmbed = discord.Embed(title="Close Command Used:", color=0xBA2100)

    if validUseOfCommand == True:
        # Logging

        logEmbed.description = f'{ctx.author.mention} closed {currentChannel}'

        await currentChannel.send(':closed_lock_with_key:')
        await currentChannel.send('Deleting this channel in 60 seconds. Remember this command does not Kick! Use '
                                  '`!reject @name` if you need the person removed from the server before this channel'
                                  ' closes!')

        # wait 60 seconds then delete the channel
        await asyncio.sleep(60)
        await currentChannel.delete() # Logging
        logger.info(f'({current_time}) CLOSE: Deleted Channel {currentChannel}')

    elif currentChannel != channel and securityTeam in author.roles:
        await currentChannel.send('`You must in the channel you want to close and mention it with the #`')
        logEmbed.description = f'{ctx.author.mention} tried to use !close in {currentChannel}.\n\n' \
                               f'They either typed the name wrong or used it in the wrong channel.'
        logger.info(f'({current_time}) CLOSE: {currentChannel} is not valid!')

    else:
        logEmbed.description = f'{ctx.author.mention} tried to use !close in {currentChannel}.\n\n' \
                               f'They either do not have the proper permissions or it was an invalid channel'
        logger.info(f'({current_time}) CLOSE: {securityTeam} role not found or {currentChannel} is not valid!')
        await currentChannel.send('`You must be a Recruiter and be in that channel to use this command.')

    await modLogChannel.send(embed=logEmbed)


@close.error
async def close_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`CLOSE: Error: {error}`')
    logger.info(f'({current_time}) CLOSE: {error}')


@bot.command(aliases=['bot', 'commands', 'fuckingbot', 'help', "recruiter", "recruit", "rHelp", "rhelp", "security",
                      "verifyhelp"])
async def command(ctx):
    author = ctx.author
    guild = ctx.guild

    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

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
    helpEmbed.add_field(name="!nato {SystemName}", value="Will translate the name of a system to Phonetic Nato - !nato"
                                                         " 8-SPNN -> EIGHT -TAC- SIERRA PAPA NOVEMBER NOVEMBER")
    helpEmbed.add_field(name="!ghDiscord", value="Will get you a link to the Golden Horde Discord")
    helpEmbed.add_field(name="!channelPass", value="Will display the last known in-game channel passwords. (Aliases: "
                                                   "!password | !channel | and lots of others")
    helpEmbed.add_field(name="!hemp {ore_emoji} #", value="For HEMP donations. Put all your ore in at once, like:\n\n"
                                                          "!hemp :spodumain: 1000 :veldspar: 1000")

    recruitHelpEmbed = discord.Embed(title="Recruiter Commands", color=0xFFFFFF)
    recruitHelpEmbed.description = 'These are the Following Commands that you can use on HOME at the Recruiter level'
    recruitHelpEmbed.add_field(name="!verify @name",
                               value='Only usable in the private channels auto generated by the bot on a new user join. '
                                     'It will remove the Applicant and Just Joined! roles and assign Associate. It will'
                                     'send a welcome message to the general chat and a useful new rules DM to the one '
                                     'mentioned. It will delete the room in 15 seconds. If done correctly you will see'
                                     'CONCORD-Bot respond with :white-check-mark:', inline=False)
    recruitHelpEmbed.add_field(name="!reject @name",
                               value='Only usable in the private channels auto generated by the bot on a new user join. '
                                     'It will remove the channel and kick the user mentioned after 15 seconds. It will '
                                     'send a DM to the user kicked explaining what happened.', inline=False)
    recruitHelpEmbed.add_field(name="!close #channnel-name",
                               value='Only usable in the private channels auto generated by the bot on a new user join. '
                                     'It will remove the channel - THERE IS NO KICK with this command. It is for use '
                                     'when a user leaves before the !reject command can be used', inline=False)
    directorEmbed = discord.Embed(title="Director Commands", color=0xFFFFFF)
    directorEmbed.description = 'These are the Following Commands that you can use on HOME at the Director level'
    directorEmbed.add_field(name="!kick @name reason",
                               value='Only useable at the Director Level, will kick a member from the server, log the '
                                     'use in #modlogs and send a DM with the reason entered', inline=False)

    if ctx.guild.get_role(int(VERIFIED)) not in author.roles:
        return
    else:
        await ctx.channel.send(f'Bot Commands are on their way to your DM\'s {author.mention}')
        await author.send(embed=helpEmbed)
        logger.info(f'({current_time}) HELP: {author.name} used the help command')

    if ctx.guild.get_role(int(SECURITY)) in author.roles:
        await author.send(embed=recruitHelpEmbed)

    if ctx.guild.get_role(KICK) in author.roles:
        await author.send(embed=directorEmbed)

@command.error
async def command_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`COMMAND/HELP: Error: {error}`')
    logger.info(f'({current_time}) COMMAND/HELP: {error}')


@bot.command(name='Skynet')
async def skynet(ctx, message):
    author = ctx.author
    generalchat = get(ctx.guild.text_channels, id=GENERAL)

    if author.id == int(182249916087664640):
        await generalchat.send(message)


@bot.command(name='corp')
async def corp(ctx):
    author = ctx.author
    channel = ctx.channel

    now = datetime.today()

    current_time = now.strftime("%H:%M:%S")

    cardEmbed = discord.Embed(title="In Game Corp", description="How to find HOME in game.")
    cardEmbed.add_field(name="HOME - Up to 2 clones per player (subject to change)",
                        value=" Search for HOME or 1000000581", inline=False)
    cardEmbed.add_field(name="HOM2 - All your other Alts",
                        value=" Search for HOM2 or 1000008117", inline=False)
    cardEmbed.set_image(url="https://cdn.discordapp.com/attachments/743284961225998406/762367195334049882/unknown.png")

    await channel.send(embed=cardEmbed)
    logger.info(f'({current_time}) CORP: {author.name} used the corp buisness card command in #{channel}')

@corp.error
async def corp_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`CORP: Error: {error}`')
    logger.info(f'({current_time}) CORP: {error}')


@bot.command(name="kick")
async def kick(ctx, member: discord.member, *, message: str = "None Provided"):
    author = ctx.author
    guild = ctx.guild
    modLogChannel = guild.get_channel(MODLOG)

    now = datetime.today()

    # Create the MODLOG channel embed
    logEmbed = discord.Embed(title="KICK Command Used;", color=0x870404)

    if ctx.guild.get_role(KICK) not in author.roles:
        logger.info(f'{now} KICK: {author.mention} tried to use KICK but does not have the appropriate permissions')
        logEmbed.description = f'{author.mention} tried to use the Kick command but did not have the proper role'
        return
    else:
        # React to the command usage

        # DM the member
        await member.send(f"You have been removed from the HOME server. {message}")

        # Logging
        logger.info(f'({now}) KICK: {author.mention} has Kicked {member.display_name} with {message} reason')
        logEmbed.description = f'{author.mention} kicked {member.display_name} with the reason of {message}'

        #Kick
        await guild.kick(member, reason=f"{message} as entered by {author.display_name}")

    await modLogChannel.send(embed=logEmbed)


@kick.error
async def kick_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`KICK: Error: {error}`')
    logger.info(f'({current_time}) KICK: {error}')


@bot.command(name='lynksmoa')
async def lynksmoa(ctx):

    startDate = datetime.fromtimestamp(1603066735)

    currentDate = datetime.today()

    stringDate = currentDate.strftime('%Y-%m-%d %H:%M:%S')

    difference = currentDate-startDate

    days = divmod(difference.total_seconds(), 86400)
    hours = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)

    embed = discord.Embed(title="Lynk's Moa - How long has it lasted?", color=0x2EA7DB,
                          description="Lynk is on Moa number 5, a standard T6 Moa. It came first came online on "
                                      "2020.19.10 around 00:20 UTC")

    embed.add_field(name="It has been...",
                    value=f'{days[0]} days,  {hours[0]} hours, and {minutes[0]} minutes since Lynk got his latest Moa.',
                    inline=False)

    embed.add_field(name="Moa #1", value="Lost to T7 Deadspace ~ 2 weeks")
    embed.add_field(name="Moa #2", value="Lost to T7 Anomoly in ~ 24 hours")
    embed.add_field(name="Moa #3", value="Lost to Scout Gankers in < 12hours")
    embed.add_field(name="Moa #4", value="Lost to T7 Encounter LAG in 4 Days 22 hours (but returned via ticket!)")
    embed.add_field(name="Moa #4.5", value="Lost to Greys in defense of m53 when the game crashed. in 10 days 10 hours")

    await ctx.channel.send(embed=embed)
    logger.info(f'({currentDate}) LYNKSMOA: {ctx.author} used the lynksmoa command')


@bot.command(aliases=["channelPass", "channelpass", "channel", "m53defense", "p74", "ghc", "password", "passwords",
             "channelPasswords", "channelpassword", "pass", "Channelpass", "ChannelPass", "ChannelPasswords", "channels"])
async def channel_password(ctx):
    author = ctx.author
    guild = ctx.guild
    now = datetime.today()

    if guild.get_role(int(VERIFIED)) not in author.roles:
        return
    else:
        passwordEmbed = discord.Embed(title="In Game Channels and Passwords", color=0x000000)
        passwordEmbed.description = "This Command last Updated 2020.18.10. If incorrect message Lynkfox and check the" \
                                    " Golden Horde Discord #ingame-channels.\n\nFormat: " \
                                    "Description, ```channelName - password```"
        passwordEmbed.add_field(name="Intel Channels", value="For Grey/Red Sightings and movement reports. No idle "
                                                             "chat. General Cache Intel ```p74 - 79048```"
                                                             "M53 Miner Defense Intel ```m53defense - 77981```"
                                                             "Germinate Intel ```GemIntel - 6771```"
                                                             "Outpost Defense Callouts ```8spnn - 33831```", inline=False)
        passwordEmbed.add_field(name="General Chat", value="Chatting and Fleet up"
                                                           "General Chat ```GHC - 8287```"
                                                           "Germinate Chat ```nsf1 - 0402```", inline=False)
        passwordEmbed.add_field(name="Fleeting Up", value="Often CTA's will ask you to x up in a chat channel. Because"
                                                          " of the size of our alliance, once you have joined a fleet "
                                                          "please leave the channel to allow others to get in and x up.",
                                inline=False)
        passwordEmbed.add_field(name="LFG Channels", value="`HordeLFG`, `CacheLFG`, `GemLFG`, password all `1111`")

        onItsWay = discord.Embed(title="", color=0x000000, description=f'Channel Passwords Messaged to you, '
                                                                       f'{author.mention}')
        await author.send(embed=passwordEmbed)
        await ctx.channel.send(embed=onItsWay)
        logger.info(f'({now}) CHANNEL_PASSWORD: {ctx.author} used the channelPass command')


@channel_password.error
async def channel_password_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`CHANNELPASSWORD: Error: {error}`')
    logger.info(f'({current_time}) CHANNELPASSWORD: {error}')


@bot.command(name="nato")
async def nato(ctx, system:str):
    natoAlphabet = { 'A':'Alfa',
                     'B':'Bravo',
                     'C':'Charlie',
                     'D':'Delta',
                     'E':'Echo',
                     'F':'Foxtrot',
                     'G':'Golf',
                     'H':'Hotel',
                     'I':'India',
                     'J':'Juliet',
                     'K':'Kilo',
                     'L':'Lima',
                     'M':'Mike',
                     'N':'November',
                     'O':'Oscar',
                     'P':'Papa',
                     'Q':'Quebec',
                     'R':'Romeo',
                     'S':'Sierra',
                     'T':'Tango',
                     'U':'Unicorn',
                     'V':'Victor',
                     'W':'Whisky',
                     'X':'X-Ray',
                     'Y':'Yankee',
                     'Z':'Zulu',
                     '-':'-tac-',
                     '0':'Zero',
                     '1':'One',
                     '2':'Two',
                     '3':'Three',
                     '4':'Four',
                     '5':'Five',
                     '6':'Six',
                     '7':'Seven',
                     '8':'Eight',
                     '9':'Niner'
                     }
    word = list(str(system))
    channel = ctx.channel
    author = ctx.author
    now = datetime.today()

    translated = "Translated: "
    for letter in word:
        translated += natoAlphabet[letter.upper()].upper() + " "

    embed = discord.Embed(title="Nato Translation", color=0x00E8FF)
    embed.description=f'{system.upper()} {translated}'

    await channel.send(embed=embed)

    logger.info(f'({now}) NATO: {ctx.author} used the NATO command on {system}')


@nato.error
async def nato_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`NATO: Error: {error}`')
    logger.info(f'({current_time}) NATO: {error}')


@bot.command(name="nick")
async def nick(ctx, *nickname):
    guild = ctx.guild
    channel = ctx.channel
    author = ctx.author
    roles = ""
    roleLog = ""
    newNick = ""
    combat = guild.get_role(COMBAT)
    mining = guild.get_role(MINING)

    now = datetime.today()

    if nickname is None:
        await channel.send("```You need to provide a nickname```")
        return

    # TODO: deny if has the star or spade or [ ] in it already.

    if combat in author.roles:
        roles += "-♤"
        roleLog += f'{combat.mention}\n'

    if mining in author.roles:
        roles += "-☆"
        roleLog += f'{mining.mention}\n'

    for word in nickname:
        newNick += word + " "

    if mining in author.roles or combat in author.roles:
        newNick = roles + "-" + newNick[:-1]


    setEmbed = discord.Embed(title="Nickname Changed", color=0xD1FF00,
                             description=f'{author.display_name}, I\'ve changed your nick to {newNick}')

    logEmbed = discord.Embed(title="Nickname Changed", color=0xB50094,
                             description=f'{author.display_name} changed their nick to {newNick}')
    logEmbed.add_field(name="Special Nickname Roles", value=roleLog)


    await author.edit(nick=newNick)
    await channel.send(embed=setEmbed)
    logger.info(f'({now}) NICK: {ctx.author} used the NICK command: New Nickname: {newNick}')

@nick.error
async def nick_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`NICK: Error: {error}`')
    logger.info(f'({current_time}) NICK: {error}')


@bot.command(name="badge")
async def add_badge(ctx, member: discord.Member = None, role: str = None):
    guild = ctx.guild
    channel = ctx.channel
    author = ctx.author
    currentNickname = member.display_name
    modLogChannel = guild.get_channel(MODLOG)
    director = guild.get_role(KICK)
    roles = ""
    combat = guild.get_role(COMBAT)
    mining = guild.get_role(MINING)

    now = datetime.today()

    if director not in author.roles:
        return

    if role.lower() == 'ace':
        roles = "-♤-"
        await member.add_roles(combat, reason="Promote Command")

    if role.lower() == 'hemp':
        roles = "-☆-"
        await member.add_roles(mining, reason="Promote Command")

    if mining in member.roles and combat in member.roles:
        roles = "-♤-☆-"

    newNick = roles+currentNickname

    setEmbed = discord.Embed(title=f'{role} Assigned!', color=0xD1FF00,
                             description=f'{author.display_name}, {currentNickname} has been promoted to {role}.'
                                         f' New Nickname: {newNick}')

    logEmbed = discord.Embed(title=f"{role} Assigned", color=0xB50094,
                             description=f'{author.display_name} promoted {currentNickname} to {role}. .')

    await author.edit(nick=newNick)
    await channel.send(embed=setEmbed)
    await modLogChannel.send(embed=logEmbed)
    logger.info(f'({now}) PROMOTE: {ctx.author} promoted {member.display_name} to {roles}"')


@add_badge.error
async def add_badge_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`BADGE: Error: {error}`')
    logger.info(f'({current_time}) BADGE: {error}')


@bot.command(name='hemp')
async def hemp(ctx, *buyback):
    guild = ctx.guild
    channel = ctx.channel
    author = ctx.author
    now = datetime.today()
    hemp_channel = guild.get_channel(DONATION)
    error_channel = guild.get_channel(ERROR)
    mod_log_channel = guild.get_channel(MODLOG)

    buyback_volume = 0

    size_values = {'veldspar': .1,
                   'plagioclase': .35,
                   'scordite': .15,
                   'omber': .6,
                   'pyroxeres': 1.5,
                   'kernite': 1.2,
                   'darkochre': 1.6,
                   'gneiss': 2,
                   'spodumain': 3.2,
                   'hemorphite': 3,
                   'hedbergite': 3,
                   'jaspert': 4,
                   'crokite': 6.4,
                   'bistot': 6.4,
                   'arkonor': 6.4,
                   'mercoxit': 8}

    total_ores = dict()

    buyback_embed = discord.Embed(title=f"HEMP donation for {author.display_name}", color=0xE58700)

    if buyback is None or buyback[0].isnumeric() or len(buyback) < 2 or buyback[1] is None:
        await channel.send('`You must use the format of :ore: # for all your ores at once. Use the emoji!`')
        return

    for entry in buyback:
        if not entry.isnumeric():
            try:
                ore = entry.split(':')[1]
                unit_volume = size_values[ore.lower()]
            except KeyError:
                await channel.send(f'`You must use the emoji for the ore, from this server - {ore} is invalid`')
                logger.warning(f'({now}) HEMP: {ctx.author} - {ore} invalid')

                return
            except IndexError:
                await channel.send(f'`{entry} is an invalid flag for this command`')
                logger.warning(f'({now}) HEMP: {ctx.author} - {entry} invalid')
                return
            except Exception as e:
                logger.warning(f'({now}) HEMP: {ctx.author} - {e}')
                await error_channel.send(f'`HEMP command failed - Exception {e}`')
                return

            ore_index = buyback.index(entry)
            amount = buyback[ore_index+1]
            if not amount.isnumeric():
                await channel.send(f'`You must use numbers in the amounts: {amount} for {ore} is a bad value.`')
                return

            total_volume = unit_volume * int(amount)
            single_ore = [amount, total_volume]
            total_ores[ore] = single_ore
            buyback_volume += total_volume

            if ore == 'darkochre':
                ore = 'Dark Ochre'

            buyback_embed.add_field(name=f'{entry} {ore.capitalize()}',
                                    value=f'x{amount} : ( {total_volume} m³ ) ')
            await ctx.message.add_reaction(entry)

    buyback_embed.description = f'**Total Volume Turned In** : {buyback_volume}\nOn {now.strftime("%A, %B %d %Y")}'

    await hemp_channel.send(embed=buyback_embed)
    mod_embed = discord.Embed(title=f'{author} HEMP Donation',
                              description=f'{buyback_volume} - On {now.strftime("%A, %B %d %Y")}')
    mod_embed.add_field(name='Ores - {Ore Name : [\'Units\', volume]}',
                        value=total_ores)
    await mod_log_channel.send(embed=mod_embed)

    logger.info(f'({now}) HEMP: {ctx.author} used the HEMP command for a total of {buyback_volume} m3"')


@hemp.error
async def hemp_error(ctx, error):
    now = datetime.today()
    error_channel = ctx.guild.get_channel(ERROR)

    current_time = now.strftime("%H:%M:%S")

    await error_channel.send(f'`HEMP: Error: {error}`')
    logger.info(f'({current_time}) HEMP: {error}')


bot.run(TOKEN)
