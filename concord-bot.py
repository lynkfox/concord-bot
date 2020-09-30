import os
import logging
import discord
import asyncio
import datetime
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VERIFIED = int(os.getenv('VERIFIED_ROLE'))
MODLOG = int(os.getenv('MOD_CHANNEL'))
SECURITY = int(os.getenv('SECURITY_ROLE'))
CHECKPOINT = int(os.getenv('CHECKPOINT_CAT'))
GENERAL = int(os.getenv('GENERAL_CHAT'))
JOINLEAVE = int(os.getenv('ENTRY_EXIT_CHANNEL'))
NEWB = int(os.getenv('NEWBIE_ROLE'))

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
    tempName = str(member).replace(' ', '-').replace('#', '').lower()
    mention = member.mention
    securityRole = guild.get_role(int(SECURITY))

    # Set of permissions for the new channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        securityRole: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                                  read_message_history=True),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True,
                                            read_message_history=True)

    }
    # TO DO - Remove Hard coded role id and checkpoint category name
    tempChannel = await guild.create_text_channel(tempName, overwrites=overwrites)

    # Get the category for the checkpoint
    for category in guild.categories:
        if category.id == CHECKPOINT:
            await tempChannel.edit(category=category)
            logger.info(f'ON_MEMBER_JOIN: {member} joined, Channel Created {tempChannel} under {category}')

    await tempChannel.send(f'{mention}, Welcome! You are new to our server! Here is a private channel for us to '
                           'interview you.')
    await tempChannel.send(f'We take security very seriously here!\n\nOne of our {securityRole.mention} Staff will be '
                           'along to aid you soon. In the meantime, check out the #welcome-to-home channel and select '
                           'your reason for being here. Then you can chat in the #welcome-lobby\n\nIf You are applying '
                           'to HOME, you can speed up the process by posting an in game screenshot of your entire '
                           'character sheet. Thanks!')

    # Server Entry Exit Logging

    logEmbed = discord.Embed(title="New Member Joined", color=0x00A71E)
    logEmbed.description = f'{member.mention} ( {member.name} ) has joined the server'
    logEmbed.add_field(name='Create Date', value=member.created_at)
    logEmbed.add_field(name='Private Channel', value=tempName)
    logEmbed.set_thumbnail(url=member.avatar_url)

    # check if account less than 7 days old
    oneWeekAgo = datetime.date.Today() - datetime.timedelta(days=7)
    if member.created_at > oneWeekAgo:
        securityRole = guild.get_role(int(SECURITY))
        logEmbed.add_field(name='WARNING', value=f'{securityRole.mention} this account is less than 7 days old')

    guild.get_channel(JOINLEAVE).send(embed=logEmbed)






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
        logger.info(f'VERIFY: {ctx.author.display_name} failed to use command on {member.name} because they don\'t have '
                    f'the {securityRole.name} role')

    # if its used in the wrong channel, log that.
    elif ctx.channel.name is not tempName:
        logEmbed.description = f'{ctx.author.mention} tried to use !verify on {member.mention} in channel ' \
                               f'#{ctx.channel.name} and this is not an approved channel.'
        await ctx.guild.get_channel(MODLOG).send(embed=logEmbed)

        logger.info(f'VERIFY: {ctx.author.display_name} failed to use command on {member.name} in an inappropriate'
                    f' channel, {ctx.channel.name}')



#@verify.error
#async def verify_error(ctx, error):
#   if isinstance(error, commands.BadArgument):
#        await ctx.send('I could not find that member... (be sure to use @Name and use the quick mention!)')


@bot.command(name='test')
async def test(ctx, member: discord.Member):
    welcomeEmbed = discord.Embed(title="Welcome!", color=0xBA2100,)
    welcomeEmbed.set_thumbnail(url=member.avatar_url)
    welcomeEmbed.description = f'{ctx.author.display_name} tried to use !verify on {member.name} but they do not have ' \
                           f'the  role'

    await ctx.channel.send(embed=welcomeEmbed)



bot.run(TOKEN)
