import datetime
import discord
import time
from discord.ext import commands

from main import InviteMonitor


class Setting(commands.Cog):
    """__SetUp the bot__"""

    def __init__(self, bot):
        self.bot = bot  # type: InviteMonitor

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f":hourglass_flowing_sand: Interval too fast!\nYou can use this command again __**after {error.retry_after:.2f} sec!**__")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(":placard: Missing required arguments!")
        else:
            await ctx.send(f":tools: Unexpected error has occurred. please contact to bot developer.\n```py{str(error)[:1900]}```")

    @commands.command(usage="enable (#channel)", description="Start monitor invites and report logs to specified channel. If no channel provided, set to command executed channel.")
    async def enable(self, ctx):
        # 設定前に権限を確認
        if not self.bot.check_permission(ctx.guild.me):
            return await ctx.send(":no_entry_sign: Missing required permission **__manage_guild__**!\nPlease make sure that BOT has right access.")
        if not self.bot.check_permission(ctx.author):
            return await ctx.send(":no_pedestrians: You don't have **__manage_guild__** permission!\nFor security reasons, this command can only be used by person who have permission.")
        # 対象チャンネルを取得
        target_channel: discord.TextChannel
        if not len(ctx.message.channel_mentions):
            target_channel = ctx.channel
        else:
            target_channel = ctx.message.channel_mentions[0]
        # チャンネルデータを保存
        self.bot.db[str(ctx.guild.id)]["channel"] = target_channel.id
        await ctx.send(f":chart_with_upwards_trend: Log channel has been set to {target_channel.mention} successfully!\nNow started to monitor invites and report logs.")

    @commands.command(usage="disable", description="Stop both monitoring and reporting information in the server.")
    async def disable(self, ctx):
        # 設定前に権限を確認
        if not self.bot.check_permission(ctx.guild.me):
            return await ctx.send(":no_entry_sign: Missing required permission **__manage_guild__**!\nPlease make sure that BOT has right access.")
        if not self.bot.check_permission(ctx.author):
            return await ctx.send(":no_pedestrians: You don't have **__manage_guild__** permission!\nFor security reasons, this command can only be used by person who have permission.")
        self.bot.db[str(ctx.guild.id)]["channel"] = None
        await ctx.send(f":chart_with_downwards_trend: Stopped monitoring and reporting information.\nYou can resume with `{self.bot.PREFIX}enable` command at any time!")

    @commands.command(aliases=["st"], usage="status (@user)", description="Show user's information includes inviter and invite counts. If no user mentioned, server status will be displayed.")
    async def status(self, ctx):
        # そのサーバーでログが設定されているか確認
        if self.bot.db[str(ctx.guild.id)]["channel"] is None:
            return await ctx.send(f":warning: Monitoring not enabled! Please setup by `{self.bot.PREFIX}enable` command before checking status.")
        if not ctx.message.mentions:
            # 設定を取得
            embed = discord.Embed(title=":chart_with_downwards_trend: Log Settings Status", color=0x9932cc)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.description = f"Status of the server **{ctx.guild.name}**"
            embed.add_field(name="Log Channel", value=f"<#{self.bot.db[str(ctx.guild.id)]['channel']}>")
            embed.add_field(name="Member Count", value=f"{len(ctx.guild.members)}")
            embed.add_field(name="Known Members", value=f"{len(self.bot.db[str(ctx.guild.id)]['users'])}")
            embed.add_field(name="Invites Count", value=f"{len(self.bot.cache[ctx.guild.id])}")
            await ctx.send(embed=embed)
        else:
            target_user = ctx.message.mentions[0]
            embed = discord.Embed(title=f":clipboard: {str(target_user)}", color=0xffff00)
            embed.set_thumbnail(url=target_user.avatar_url)
            if str(target_user.id) in self.bot.db[str(ctx.guild.id)]["users"]:
                remain_count = 0
                if self.bot.db[str(ctx.guild.id)]["users"][str(target_user.id)]["to"] is not None:
                    remain_count = len(self.bot.db[str(ctx.guild.id)]["users"][str(target_user.id)]["to"])
                total_count = 0
                # TODO: to_all廃止によりmembersと照会して取得
                # if self.bot.db[str(ctx.guild.id)]["users"][str(target_user.id)]["to_all"] is not None:
                #     total_count = len(self.bot.db[str(ctx.guild.id)]["users"][str(target_user.id)]["to_all"])
                total_count = 0  # エラー一時回避
                embed.add_field(name="Invite Count", value=f"{remain_count} / {total_count}")
                if (inviter_id := self.bot.db[str(ctx.guild.id)]["users"][str(target_user.id)]["from"]) is not None:
                    if (inviter := self.bot.get_user(inviter_id)) is None:
                        try:
                            inviter = await self.bot.fetch_user(inviter_id)
                        except:
                            inviter = "Unknown"
                    embed.add_field(name="Invited By", value=str(inviter))
                else:
                    embed.add_field(name="Invited By", value="Unknown")
            else:
                embed.add_field(name="Invite Count", value="0 / 0")
                embed.add_field(name="Invited By", value="Unknown")
            embed.add_field(name="Joined At", value=ctx.guild.get_member(target_user.id).joined_at.strftime("%Y/%m/%d %H:%M:%S"))
            await ctx.send(embed=embed)

    @commands.command(usage="about", description="Show the information about his BOT")
    async def about(self, ctx):
        embed = discord.Embed(title=f"About {self.bot.user.name}", color=0xffe4b5)
        embed.description = f"""**Thank you for using {self.bot.user.name}!**
> InvStat is strong server invites monitoring bot that allows you to
> ・ know inviter of participant
> ・ counts people invited by a particular user
> ・ kick users who invited by specified troll user
> It protects your server from malicious users and manage private server invitations for security! 🔐"""
        embed.add_field(name="Discord", value=f"```Server Count: {len(self.bot.guilds)}\nUser Count: {len(self.bot.users)}\nLatency: {self.bot.latency:.2f}[s]```")
        td = datetime.timedelta(seconds=int(time.time() - self.bot.uptime))
        m, s = divmod(td.seconds, 60)
        h, m = divmod(m, 60)
        d = td.days
        embed.add_field(name="Uptime", value=f"{d}d {h}h {m}m {s}s", inline=False)
        embed.add_field(name="URL 📎", value=f"[InviteBOT]({self.bot.static_data.invite}) | [OfficialServer]({self.bot.static_data.server})", inline=False)
        embed.set_footer(text=f"{self.bot.user.name} is powered by {self.bot.get_user(self.bot.static_data.author)} with discord.py", icon_url="http://zorba.starfree.jp/mafu.jpg")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Setting(bot))
