import discord.ext import commands

@commands.command()
async def add_badge(ctx, member: discord.member, role):
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

    if role.lower() == combat:
        roles = "-♤-"
        await member.add_roles(combat, reason="Promote Command")

    if role.lower == mining:
        roles = "-☆-"
        await member.add_roles(mining, reason="Promote Command")

    if mining in member.roles and combat in member.roles:
        roles = "-♤-☆-"

    newNick = roles+currentNickname

    setEmbed = discord.Embed(title=f'{role} Assigned!', color=0xD1FF00,
                             description=f'{author.display_name}, {currentNickname} has been promoted to {role.name}.'
                                         f' New Nickname: {newNick}')

    logEmbed = discord.Embed(title=f"{role} Assigned", color=0xB50094,
                             description=f'{author.display_name} promoted {currentNickname} to {role.name}. .')

    await author.edit(nick=newNick)
    await channel.send(embed=setEmbed)
    await modLogChannel.send(embed=logEmbed)
    logger.info(f'({now}) PROMOTE: {ctx.author} promoted {member.display_name} to {roles}"')