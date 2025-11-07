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
        description="Đặt món ăn từ thực đơn Noel đặc biệt",
    )
    async def order(self, context: Context) -> None:
        """
        Đặt món ăn Noel sử dụng hình ảnh thực đơn.

        :param context: The application command context.
        """
        delete_cd_time = var_global.cd_time
        
        message = context.message
        if message.attachments.__len__() != 1:
            embed = discord.Embed(
                title="🎄❄️ Santa cần hình ảnh thực đơn Noel! ❄️🎄",
                description=f"""
```
╔══════════════════════════════════╗
║     🎅 THÔNG BÁO TỪ SANTA 🎅     ║
║                                  ║
║  Ho ho ho! Tôi cần một hình ảnh  ║
║   thực đơn để chuẩn bị bữa tiệc  ║
║        Noel đặc biệt cho bạn!    ║
║                                  ║
║      🎁 Hãy gửi ảnh ngay! 🎁      ║
╚══════════════════════════════════╝
```

🌟 **Noel đang đến rất gần rồi!** Hãy nhanh chóng đính kèm hình ảnh thực đơn để chúng ta có thể bắt đầu chuẩn bị bữa tiệc thần tiên! ✨
""",
                color=0xC41E3A,
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
            embed.set_image(url="https://images.unsplash.com/photo-1512389098783-66b81f86e199?w=600&h=200&fit=crop")
            await context.reply(embed=embed, ephemeral=True)
            return
        
        # Magical Christmas loading message with countdown feeling
        import datetime
        now = datetime.datetime.now()
        days_to_christmas = 25 - now.day if now.month == 12 else 31 - now.day + 25
        
        loading_messages = [
            f"🎅 Santa đang đọc thực đơn Noel của bạn...",
            f"🎄 Elf đang chuẩn bị phép màu Giáng Sinh...",
            f"⭐ Đang tìm kiếm các món ăn kỳ diệu...",
            f"❄️ Bông tuyết đang mang tin vui Noel đến...",
            f"🔔 Chuông Giáng Sinh đang vang lên..."
        ]
        
        loading_embed = discord.Embed(
            title="🎄✨ PHÉP MÀU NOEL ĐANG DIỄN RA ✨�",
            description=f"""
```diff
+ 🌟 SANTA'S WORKSHOP ĐANG HOẠT ĐỘNG 🌟
```

{loading_messages[now.second % len(loading_messages)]}

⏳ **Chỉ còn {days_to_christmas} ngày nữa là Noel!** 
❄️ **Không khí lễ hội** đang bao trùm mọi nơi...
🎁 **Món quà đặc biệt** đang được chuẩn bị...

```
Ho ho ho! Vui lòng đợi trong giây lát... ✨
```
""",
            color=0x228B22
        )
        loading_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
        loading_embed.set_image(url="https://images.unsplash.com/photo-1576020799627-aeac74d58064?w=600&h=200&fit=crop")
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
                error_embed = discord.Embed(
                    title="🎄 Lỗi phân tích thực đơn Noel",
                    description=f"Santa không thể đọc được thực đơn: {e}\n\nVui lòng thử lại với hình ảnh rõ ràng hơn!",
                    color=0xC41E3A
                )
                error_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
                try:
                    await pending_message.edit(embed=error_embed)
                except discord.NotFound:
                    await context.send(embed=error_embed, ephemeral=True)
                return

            await pending_message.delete()
            
            # Magical Christmas success notification
            celebration_messages = [
                f"🎅 Ho ho ho! Santa đã chuẩn bị {len(menu)} món ăn kỳ diệu!",
                f"🎄 Thành công! {len(menu)} món Noel đặc biệt đang chờ bạn!",
                f"⭐ Tuyệt vời! Elf đã tìm thấy {len(menu)} công thức ma thuật!",
                f"🎁 Chúc mừng! {len(menu)} món quà Noel đã sẵn sàng!"
            ]
            
            import datetime
            now = datetime.datetime.now()
            success_message = celebration_messages[now.second % len(celebration_messages)]
            
            success_embed = discord.Embed(
                title="🎄✨ PHÉP MÀU NOEL ĐÃ THÀNH CÔNG! ✨🎄",
                description=f"""
```diff
+ � SANTA'S WORKSHOP ĐÃ HOÀN TẤT! 🌟
```

{success_message}

```ansi
╔══════════════════════════════════╗
║    🎅 BỮA TIỆC NOEL SẴN SÀNG! 🎅  ║
║                                  ║
║   ❄️ Không khí lễ hội đang lan   ║
║      tỏa khắp mọi nơi! ❄️        ║
║                                  ║
║  🎁 Hãy bắt đầu đặt món ngay! 🎁  ║
╚══════════════════════════════════╝
```

🔔 **Chuông Giáng Sinh đang vang lên báo hiệu bữa tiệc bắt đầu!**
✨ **Mỗi món ăn đều chứa đựng phép màu của mùa Noel!** ✨
""",
                color=0x228B22
            )
            success_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
            success_embed.set_image(url="https://images.unsplash.com/photo-1544456850-4eb1f1fc7df8?w=600&h=200&fit=crop")
            temp_msg = await context.send(embed=success_embed, delete_after=delete_cd_time)
            
            view = MenuView(menu, context)
            embed = view.create_menu_embed()
            view.message = await context.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"Error in order command: {e}")
            error_embed = discord.Embed(
                title="❄️ Đã xảy ra lỗi Noel",
                description=f"Oops! Santa gặp sự cố: `{e}`\n\nVui lòng thử lại với hình ảnh thực đơn Noel rõ ràng hơn!",
                color=0xC41E3A
            )
            error_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
            try:
                await pending_message.edit(embed=error_embed)
            except discord.NotFound:
                # If pending message was deleted, send a new error message
                await context.send(embed=error_embed, ephemeral=True)

    @commands.hybrid_command(
        name="finalize_order",
        description="Chốt tất cả đơn hàng Noel (Chỉ Admin)",
    )
    @commands.has_permissions(administrator=True)
    async def finalize_order(self, context: Context) -> None:
        """
        Chốt tất cả đơn hàng Noel - chỉ dành cho admin.

        :param context: The application command context.
        """
        # This is an alternative way to finalize orders via slash command
        # Check if there's an active order menu
        if not hasattr(self.bot, 'active_order_view') or self.bot.active_order_view is None:
            embed = discord.Embed(
                title="🎄 Không tìm thấy thực đơn Noel",
                description="Vui lòng sử dụng lệnh `/order` với hình ảnh thực đơn Noel trước!",
                color=0xE67E22
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
            await context.reply(embed=embed, ephemeral=True)
            return
            
        # Get the active order view
        active_view = self.bot.active_order_view
        
        # Check if there are any orders
        if not active_view.user_orders:
            embed = discord.Embed(
                title="🎁 Chưa có đơn hàng Noel",
                description="Không có đơn nào để chốt. Santa đang chờ mọi người đặt món Noel!",
                color=0xE67E22
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
            await context.reply(embed=embed, ephemeral=True)
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
