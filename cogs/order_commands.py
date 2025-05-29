import json
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from ai_models.google_ai import GoogleAI
from views.order_menu import MenuView
from utils import var_global  # Fixed import path

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
        delete_cd_time = var_global.cd_time
        
        message = context.message
        if message.attachments.__len__() != 1:
            embed = discord.Embed(
                title="📸 **Thiếu hình ảnh thực đơn**",
                description="🤖 Vui lòng đính kèm **một hình ảnh** thực đơn để tôi có thể phân tích và tạo đơn hàng cho bạn!",
                color=0xE02B2B,
            )
            embed.add_field(
                name="💡 **Hướng dẫn:**",
                value="1️⃣ Chụp ảnh thực đơn rõ ràng\n2️⃣ Đính kèm ảnh vào tin nhắn\n3️⃣ Gửi lệnh `order` cùng với ảnh",
                inline=False
            )
            embed.set_footer(text="💫 Gordon Meow Meow Service - AI Powered")
            await context.reply(embed=embed, ephemeral=True)
            return
        
        # Enhanced loading message
        loading_embed = discord.Embed(
            title="🤖 **Đang xử lý thực đơn...**",
            description="⚡ AI đang phân tích hình ảnh của bạn...\n\n🔄 *Vui lòng đợi trong giây lát...*",
            color=0x3498DB
        )
        loading_embed.set_footer(text="🚀 Powered by Google AI")
        pending_message = await context.reply(embed=loading_embed)

        try:
            attachments = context.message.attachments
            image_url = attachments[0].url
            order_human_message = self.google_ai.order_message(image_url)
            ordered_message = self.google_ai.invoke(order_human_message)

            if ordered_message is None:
                await pending_message.edit(content="Đã xảy ra lỗi khi xử lý hình ảnh với AI. Vui lòng thử lại.")
                return

            ordered_message_content = ordered_message.content.strip()

            # Better JSON parsing with error handling
            try:
                # Find JSON array in the response
                start_idx = ordered_message_content.find('[')
                end_idx = ordered_message_content.rfind(']') + 1
                
                if start_idx == -1 or end_idx == 0:
                    raise ValueError("No JSON array found in AI response")
                    
                json_str = ordered_message_content[start_idx:end_idx]
                menu = json.loads(json_str)
                
                # Validate that we have a list of strings
                if not isinstance(menu, list) or len(menu) == 0:
                    raise ValueError("Invalid menu format returned by AI")
                    
                # Filter out any non-string items
                menu = [item for item in menu if isinstance(item, str) and len(item.strip()) > 0]
                
                if len(menu) == 0:
                    raise ValueError("No valid menu items found")
                    
            except (json.JSONDecodeError, ValueError) as e:
                await pending_message.edit(content=f"Lỗi khi phân tích thực đơn: {e}. Vui lòng thử lại với hình ảnh rõ ràng hơn.")
                return

            await pending_message.delete()
            
            # Create success notification
            success_embed = discord.Embed(
                title="✅ **Thực đơn đã sẵn sàng!**",
                description="🎉 AI đã xử lý thành công! Menu đặt hàng đang được tạo...",
                color=0x00D4AA
            )
            temp_msg = await context.send(embed=success_embed, delete_after=delete_cd_time)
            
            view = MenuView(menu, context)
            embed = view.create_menu_embed()
            view.message = await context.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"Error in order command: {e}")
            error_embed = discord.Embed(
                title="❌ **Đã xảy ra lỗi!**",
                description=f"💥 Lỗi: `{e}`\n\n🔄 Vui lòng thử lại với hình ảnh rõ ràng hơn.",
                color=0xE74C3C
            )
            await pending_message.edit(embed=error_embed)

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
        
        # Check if there are any orders
        if not active_view.user_orders:
            await context.reply("Không có đơn nào để chốt!", ephemeral=True)
            return
        
        # Finalize all orders
        finalized_embed = active_view.create_finalized_order_embed()
        
        # Mark as finalized
        active_view.is_finalized = True
        await active_view.disable_ordering()
        
        # Import here to avoid circular imports
        from views.finalized_order_view import FinalizedOrderView
        copy_view = FinalizedOrderView(active_view)
        
        await context.reply(embed=finalized_embed, view=copy_view)

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot: commands.Bot) -> None:
    # Initialize an attribute to track the active order view
    if not hasattr(bot, 'active_order_view'):
        bot.active_order_view = None
    order_commands = OrderCommands(bot)
    await bot.add_cog(order_commands)
    # await bot.tree.add_command(order_commands.order)
