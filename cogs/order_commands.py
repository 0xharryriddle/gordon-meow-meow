import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from ai_models.google_ai import GoogleAI
from views.order_menu import MenuView

class OrderCommands(commands.Cog, name="order_commands"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.google_ai = GoogleAI()

    @commands.command()
    async def mimic(self, ctx, arg):
        return

    @commands.command(
        name="order",
        description="Đặt món ăn từ thực đơn hôm nay",
    )
    async def order(self, context: Context) -> None:
        """
        Đặt món ăn sử dụng hình ảnh thực đơn.

        :param context: The application command context.
        """
        message = context.message
        if message.attachments.__len__() != 1:
            embed = discord.Embed(
                title="Vui lòng cung cấp một hình ảnh của thực đơn để đặt món.",
                color=0xE02B2B,
            )
            await context.reply(embed=embed, ephemeral=True)
            return
        
        pending_message = await context.reply("Vui lòng đợi trong khi tôi xử lý thực đơn...")

        attachments = context.message.attachments
        image_url = attachments[0].url
        order_human_message = self.google_ai.order_message(image_url)
        ordered_message = self.google_ai.invoke(order_human_message)

        ordered_message_content = ordered_message.content

        # Pre-process the ordered message content
        ordered_message_content = ordered_message_content[ordered_message_content.find('['):ordered_message_content.find(']') + 1 ]

        menu = json.loads(ordered_message.content)

        await pending_message.delete()
        
        view = MenuView(menu, context)
        
        # Create a new embed for the menu
        embed = view.create_menu_embed()
        
        # Send the message and store it in the view for later updates
        view.message = await context.send(embed=embed, view=view)
    
    @commands.hybrid_command(
        name="finalize_order",
        description="Chốt tất cả đơn hàng hiện tại (Chỉ Admin)",
    )
    @commands.has_permissions(administrator=True)
    async def finalize_order(self, context: Context) -> None:
        """
        Chốt tất cả đơn hàng - chỉ dành cho admin.

        :param context: The application command context.
        """
        # This is an alternative way to finalize orders via slash command
        # Check if there's an active order menu
        if not hasattr(self.bot, 'active_order_view') or self.bot.active_order_view is None:
            embed = discord.Embed(
                title="Không tìm thấy thực đơn đang hoạt động. Sử dụng lệnh order trước để tạo thực đơn.",
                color=0xE02B2B
            )
            await context.reply(embed=embed, ephemeral=True)
            return
            
        # Get the active order view
        active_view = self.bot.active_order_view
        
        # Finalize all orders
        finalized_embed = active_view.create_finalized_order_embed()
        await context.reply(embed=finalized_embed)
        
        # Clear active orders after finalization
        active_view.user_orders = {}
        await active_view.update_public_menu()
        
        await context.send("Tất cả đơn hàng đã được chốt và xóa.", ephemeral=True)

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot: commands.Bot) -> None:
    # Initialize an attribute to track the active order view
    if not hasattr(bot, 'active_order_view'):
        bot.active_order_view = None
    order_commands = OrderCommands(bot)
    await bot.add_cog(order_commands)
    # await bot.tree.add_command(order_commands.order)
