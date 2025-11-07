import datetime
from datetime import timezone, timedelta
import discord
from discord.ext.commands import Context
from views.order_modal import OrderModal
from views.order_summary import OrderSummaryView
from views.finalized_order_view import FinalizedOrderView
from utils import var_global

# Vietnam timezone (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))

def get_vietnam_time():
    """Get current time in Vietnam timezone"""
    return datetime.datetime.now(VIETNAM_TZ)

class MenuView(discord.ui.View):
    def __init__(self, menu: list, context: Context, message_id=None):
        super().__init__(timeout=None)
        self.menu = menu
        self.context = context
        self.user_orders = {}
        self.message_id = message_id
        self.message = None
        self.order_message = None
        self.is_finalized = False
        self.delete_cd_time = var_global.cd_time
        
        # Store this view as the active one in the bot
        if hasattr(context.bot, 'active_order_view'):
            context.bot.active_order_view = self
        
        # Magical Christmas dropdown with countdown feeling
        import datetime
        now = datetime.datetime.now()
        days_to_christmas = 25 - now.day if now.month == 12 else 31 - now.day + 25
        
        christmas_placeholders = [
            f"🎄 Chỉ còn {days_to_christmas} ngày! Chọn món Noel yêu thích... 🎅",
            f"❄️ Noel đang đến gần! Hãy chọn món ăn kỳ diệu... ✨",
            f"🎁 Santa đang chờ! Chọn món để bắt đầu phép màu... 🔔",
            f"🌟 Giáng Sinh 2025 đang đến! Chọn món ăn thần tiên... 🎄"
        ]
        
        self.food_select = discord.ui.Select(
            placeholder=christmas_placeholders[now.minute % len(christmas_placeholders)],
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=food[:23] + "..." if len(food) > 23 else food,
                    value=food,
                    description=f"🎁 Thêm {food} vào giỏ Noel kỳ diệu của bạn!",
                    emoji="🥘" if "cơm" in food.lower() else 
                          "🍜" if any(x in food.lower() for x in ["bún", "phở", "miến"]) else
                          "🥩" if "thịt" in food.lower() else
                          "🐟" if "cá" in food.lower() else
                          "🍲" if "canh" in food.lower() else
                          "🥬" if "rau" in food.lower() else "🎄"
                ) for food in menu
            ]
        )
        self.food_select.callback = self.food_select_callback
        self.add_item(self.food_select)
        
        # Christmas themed buttons with festive styling
        clear_all_button = discord.ui.Button(
            label="Xóa tất cả",
            style=discord.ButtonStyle.danger,
            custom_id="clear_all_order",
            emoji="🎁",
            row=1
        )
        clear_all_button.callback = self.clear_all_order_callback
        self.add_item(clear_all_button)
        
        view_button = discord.ui.Button(
            label="Xem giỏ Noel",
            style=discord.ButtonStyle.primary,
            custom_id="view_order",
            emoji="🎅",
            row=1
        )
        view_button.callback = self.view_order_callback
        self.add_item(view_button)
        
        # Refresh button with Christmas theme
        refresh_button = discord.ui.Button(
            label="Làm mới",
            style=discord.ButtonStyle.secondary,
            custom_id="refresh_menu",
            emoji="❄️",
            row=1
        )
        refresh_button.callback = self.refresh_callback
        self.add_item(refresh_button)
        
        finalize_button = discord.ui.Button(
            label="Chốt đơn Noel",
            style=discord.ButtonStyle.success,
            custom_id="finalize_order",
            emoji="🎄",
            row=2
        )
        finalize_button.callback = self.finalize_order_callback
        self.add_item(finalize_button)

        unfinalize_button = discord.ui.Button(
            label="Mở lại đơn",
            style=discord.ButtonStyle.secondary,
            custom_id="unfinalize_order",
            emoji="🔓",
            row=2
        )
        unfinalize_button.callback = self.unfinalize_order_callback
        self.add_item(unfinalize_button)

    async def refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh button for better UX"""
        try:
            # Update the menu display
            embed = self.create_menu_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            await interaction.response.send_message(
                "🔄 Menu đã được làm mới!",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )

    async def food_select_callback(self, interaction: discord.Interaction):
        # Don't allow modifications if order is finalized
        if self.is_finalized:
            await interaction.response.send_message(
                f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        selected_food = self.food_select.values[0]
        modal = OrderModal(selected_food, self.handle_quantity)
        await interaction.response.send_modal(modal)

    async def handle_quantity(self, interaction: discord.Interaction, food_name: str, quantity: int):
        # Don't allow modifications if order is finalized
        if self.is_finalized:
            await interaction.response.send_message(
                f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        # Get user ID
        user_id = str(interaction.user.id)
        
        # Create user's order entry if it doesn't exist
        if user_id not in self.user_orders:
            self.user_orders[user_id] = {}
            
        # Update food quantity
        self.user_orders[user_id][food_name] = quantity
        
        # Update the public menu to show the new order
        await self.update_public_menu()

        await interaction.response.send_message(
            content=f"Đã chọn món ăn thành công! (Tự động xóa sau {self.delete_cd_time}s)",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )

    async def clear_order_callback(self, interaction: discord.Interaction, food_name: str, qty: int):
        if self.is_finalized:
            await interaction.response.send_message(
                f"Thực đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
        
        # Get user ID
        user_id = str(interaction.user.id)
        
        # Create user's order entry if it doesn't exist
        if user_id not in self.user_orders:
            self.user_orders[user_id] = {}
            
        # Update food quantity
        self.user_orders[user_id][food_name] = qty

        await interaction.response.send_message(
            f"Món ăn của bạn đã được xóa! (Tự động xóa sau {self.delete_cd_time}s)",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )
        # Update the public menu
        await self.update_public_menu()
        

    async def clear_all_order_callback(self, interaction: discord.Interaction):
        # Don't allow modifications if order is finalized
        if self.is_finalized:
            await interaction.response.send_message(
                f"Thực đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        user_id = str(interaction.user.id)
        
        # Remove user's orders
        if user_id in self.user_orders:
            self.user_orders.pop(user_id)
        
        await interaction.response.send_message(
            f"Tất cả món ăn của bạn đã được xóa! (Tự động xóa sau {self.delete_cd_time} giây)",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )
        
        # Update the public menu
        await self.update_public_menu()

    async def view_order_callback(self, interaction: discord.Interaction):
        # Show the current order summary to the user (ephemeral)
        user_id = str(interaction.user.id)
        
        if user_id not in self.user_orders or not self.user_orders[user_id]:
            await interaction.response.send_message(
                f"Bạn chưa đặt món ăn nào! (Tự động xóa sau {self.delete_cd_time}s)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        # Create order summary embed
        embed = self.create_order_summary_embed(interaction.user)
        
        # Create a new view for the order summary with edit/remove buttons
        # Only add modification buttons if order is not finalized
        view = None
        if not self.is_finalized:
            view = OrderSummaryView(self, interaction)
        
        # Send as ephemeral message (only visible to the user)
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )
    
    def generate_copy_text(self):
        """Generate the text format for copying the quantity summary"""
        total_items = 0
        food_totals = {}
        
        for foods in self.user_orders.values():
            for food, qty in foods.items():
                total_items += qty
                if food in food_totals:
                    food_totals[food] += qty
                else:
                    food_totals[food] = qty
        
        copy_text = "Tổng kết số lượng\n"
        for food, qty in food_totals.items():
            copy_text += f"• {food}: {qty}\n"
            
        copy_text += f"\nTổng cộng: {total_items} món"
        
        return copy_text

    async def finalize_order_callback(self, interaction: discord.Interaction):
        """Callback for finalizing all orders"""
        try:
            # Check if there are any orders
            if not self.user_orders:
                await interaction.response.send_message(
                    f"Không có đơn nào để chốt! (Tự động xóa sau {self.delete_cd_time} giây)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
                
            # Create finalized order embed
            embed = self.create_finalized_order_embed()
            
            # Mark orders as finalized
            self.is_finalized = True
            
            # Disable order modification buttons
            await self.disable_ordering()
            
            # Create a view with copy button
            copy_view = FinalizedOrderView(self)
            
            # Send the finalized order to the channel
            await interaction.response.send_message(
                f"Tất cả đơn đã được chốt! (Tự động xóa sau {self.delete_cd_time} giây)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            
            await interaction.channel.send(embed=embed, view=copy_view)
        except Exception as e:
            print(f"Error in finalize_order_callback: {e}")

    async def unfinalize_order_callback(self, interaction: discord.Interaction):
        """Callback for re-opening all orders"""
        # Check if the order is already open
        if not self.is_finalized:
            await interaction.response.send_message(
                f"Đơn đã mở rồi! (Tự động xóa sau {self.delete_cd_time} giây)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
        
        # Mark orders as open
        self.is_finalized = False
        
        # Enable dropdown and other buttons
        self.food_select.disabled = False
        for item in self.children:
            if hasattr(item, 'custom_id'):
                if item.custom_id in ["clear_all_order", "finalize_order"]:
                    item.disabled = False
                elif item.custom_id == "unfinalize_order":
                    item.disabled = True

        await self.update_public_menu()
        
        # Create success embed
        success_embed = discord.Embed(
            title="🔓 **Đơn hàng đã được mở lại!**",
            description=f"""
✅ **Trạng thái:** Đơn hàng đã được mở lại thành công
👤 **Được mở bởi:** {interaction.user.mention}
⏰ **Thời gian:** {datetime.datetime.now().strftime('%H:%M:%S')}

*Mọi người có thể tiếp tục đặt thêm món!* 🍽️
""",
            color=0x00D4AA
        )
        
        await interaction.response.send_message(
            embed=success_embed,
            ephemeral=False,
            delete_after=self.delete_cd_time * 3
        )

    async def disable_ordering(self):
        """Disable ordering functionality after finalization"""
        # Disable dropdown and finalize button, enable unfinalize button
        self.food_select.disabled = True
        for item in self.children:
            if hasattr(item, 'custom_id'):
                if item.custom_id in ["clear_all_order", "finalize_order"]:
                    item.disabled = True
                elif item.custom_id == "unfinalize_order":
                    item.disabled = False
        
        # Create a new embed indicating orders are finalized
        embed = discord.Embed(
            title="#📋 Thực đơn hôm nay - ĐÃ CHỐT ĐƠN ",
            description=f"**Ngày:** {datetime.datetime.now().strftime('%d/%m/%Y')}",
            color=0x95a5a6  # Gray color
        )
        
        # Add menu items
        menu_text = ""
        for i, item in enumerate(self.menu, 1):
            menu_text += f"**{i}.** {item}\n"
        
        embed.add_field(name="##🍽️ Món ăn có sẵn", value=menu_text, inline=False)
        
        # Add order summary
        orders_text = "Đơn đã được chốt. Không thể đặt thêm."
        embed.add_field(name="🔒 Đã đóng đơn", value=orders_text, inline=False)
        
        # Update the message
        if self.message:
            await self.message.edit(embed=embed, view=self)

    async def update_public_menu(self):
        """Update the public menu message with current orders"""
        if self.message:
            embed = self.create_menu_embed()
            await self.message.edit(embed=embed, view=self)

    def create_menu_embed(self):
        """Create a magical Christmas menu embed that brings the Christmas spirit alive"""
        # Dynamic Christmas colors based on day - making it feel like Christmas is approaching
        vn_time = get_vietnam_time()
        
        # Count down to Christmas feeling
        days_to_christmas = 25 - vn_time.day if vn_time.month == 12 else 31 - vn_time.day + 25
        christmas_countdown = f"🎅 Chỉ còn {days_to_christmas} ngày nữa là Noel! "
        
        # Christmas colors rotation for festive feeling
        christmas_colors = [0xC41E3A, 0x228B22, 0xFFD700, 0xDC143C, 0x008B00]  # Red, Green, Gold, Crimson, Dark Green
        color = christmas_colors[vn_time.minute % len(christmas_colors)]

        embed = discord.Embed(
            title="🎄✨ THỰC ĐƠN NOEL KỲ DIỆU ✨🎄",
            description=f"""
╔══════════════════════════════════╗
║  🎅🎄 CHÀO MỪNG ĐẾN VỚI NOEL! 🎄🎅  ║
╚══════════════════════════════════╝

{christmas_countdown}
📅 **Hôm nay:** {vn_time.strftime('%d/%m/%Y')} 
⏰ **Giờ Noel:** {vn_time.strftime('%H:%M')} (Vietnam)
�️ **Thời tiết:** Ấm áp và đầy yêu thương

❄️ **Không khí Noel đang lan toa khắp nơi...** ❄️
🎁 **Mỗi món ăn đều chứa đựng phép màu Giáng Sinh** 🎁
🕯️ **Hãy cùng nhau tạo nên kỷ niệm đáng nhớ** �️
""",
            color=color
        )
        
        # Christmas themed menu display
        menu_text = ""
        christmas_emojis = ["🎁", "🎄", "⭐", "🔔", "❄️", "🕯️"]
        for i, item in enumerate(self.menu, 1):
            # Add Christmas emoji and food type emoji
            christmas_emoji = christmas_emojis[i % len(christmas_emojis)]
            if "cơm" in item.lower():
                emoji = "🍚"
            elif any(x in item.lower() for x in ["bún", "phở", "miến"]):
                emoji = "🍜"
            elif "thịt" in item.lower():
                emoji = "🥩"
            elif "cá" in item.lower():
                emoji = "🐟"
            elif "canh" in item.lower():
                emoji = "🍲"
            elif "rau" in item.lower():
                emoji = "🥬"
            else:
                emoji = "🍽️"
            
            menu_text += f"`{i:02d}.` {christmas_emoji} {emoji} **{item}**\n"
        
        embed.add_field(
            name="🎄🍽️ THỰC ĐƠN GIÁNG SINH KỲ DIỆU 🍽️🎄",
            value=menu_text,
            inline=False
        )
        
        # Enhanced order display
        if self.user_orders:
            orders_text = ""
            total_by_food = {}
            user_count = len(self.user_orders)
            
            for user_id, foods in self.user_orders.items():
                user = self.context.guild.get_member(int(user_id))
                user_name = user.display_name if user else "Người dùng không xác định"
                
                for food, qty in foods.items():
                    if food in total_by_food:
                        total_by_food[food] += qty
                    else:
                        total_by_food[food] = qty
                    
                    # Add Christmas spirit to order display
                    christmas_spirit = ["🎄", "🎅", "🎁", "⭐", "❄️", "🔔"][user_count % 6]
                    orders_text += f"{christmas_spirit} **{food}** `x{qty}` 👤 *{user_name}* ✨\n"
            
            if orders_text:
                embed.add_field(
                    name=f"🎅🎁 ĐƠN HÀNG NOEL KỲ DIỆU 🎁🎅 ({user_count} người tham gia tiệc)",
                    value=f"```\n╔════ DANH SÁCH ĐẶT HÀNG ════╗\n```\n{orders_text}```\n╚═══════════════════════════╝\n```",
                    inline=False
                )
                
                # Magical Christmas totals display
                totals_text = "```\n🌟 THỐNG KÊ PHÉP MÀU NOEL 🌟\n```\n"
                total_items = 0
                for food, total in total_by_food.items():
                    total_items += total
                    # Enhanced Christmas progress visualization
                    if total >= 5:
                        progress_bar = "🎄🎄🎄🎄🎄🌟✨"
                    elif total >= 3:
                        progress_bar = "🎄🎄🎄🌟❄️❄️"
                    else:
                        progress_bar = "🎄" * total + "❄️" * (5 - total)
                    
                    totals_text += f"🎁 **{food}**: `{total} phần` {progress_bar} ✨\n"
                
                totals_text += f"\n🏆 **TỔNG CỘ NOEL**: `{total_items} món kỳ diệu` 🎅\n"
                totals_text += f"🎄 **TINH THẦN NOEL**: `Đang lan tỏa khắp nơi!` ❄️"
                
                embed.add_field(
                    name=f"📊🎄 BẢNG THỐNG KÊ GIÁNG SINH 🎄📊",
                    value=totals_text,
                    inline=False
                )
        
        # Magical Christmas status with countdown feeling
        vn_time = get_vietnam_time()
        days_to_christmas = 25 - vn_time.day if vn_time.month == 12 else 31 - vn_time.day + 25
        
        if self.is_finalized:
            status_text = f"""
```diff
+ 🔔 BỮA TIỆC NOEL ĐÃ HOÀN TẤT! 🔔
```
🎅 **Ho ho ho!** Santa đã chuẩn bị xong mọi thứ!
🎁 **Phép màu Noel** đã lan tỏa đến tất cả mọi người!
✨ **Chúc mừng Giáng Sinh** - Hãy tận hưởng khoảnh khắc kỳ diệu này!
"""
            embed.color = 0xC41E3A  # Christmas red
        else:
            status_text = f"""
```ansi
🎄 ĐANG MỞ ĐƠN - NOEL ĐANG ĐẾN GẦN! 🎄
```
⏰ **Chỉ còn {days_to_christmas} ngày nữa là Giáng Sinh!**
❄️ **Không khí lễ hội** đang bao trùm khắp nơi
🌟 **Hãy nhanh chóng đặt món** để tham gia bữa tiệc Noel!
🎁 **Mỗi món ăn** đều chứa đựng tình yêu thương của mùa lễ hội
"""
            embed.color = christmas_colors[vn_time.second % len(christmas_colors)]
            
        embed.add_field(
            name="🎅� TRẠNG THÁI PHÉP MÀU NOEL 🎄🎅",
            value=status_text,
            inline=False
        )
        
        # Magical Christmas footer with seasonal feeling
        current_time = vn_time.strftime('%H:%M')
        if self.is_finalized:
            footer_text = f"🎉 {current_time} - Bữa tiệc Noel đã sẵn sàng! Chúc mừng Giáng Sinh 2025! 🎄✨"
        else:
            if int(current_time.split(':')[0]) < 12:
                time_feeling = "☀️ Buổi sáng Noel đầy hy vọng"
            elif int(current_time.split(':')[0]) < 18:
                time_feeling = "🌤️ Buổi chiều Noel ấm áp"
            else:
                time_feeling = "🌙 Đêm Noel lung linh sao"
            footer_text = f"{time_feeling} • {current_time} • 🎅 Gordon Meow Meow Christmas Magic Service ✨"
            
        embed.set_footer(
            text=footer_text,
            icon_url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png"
        )
        
        # Add Christmas feast banner image
        embed.set_image(url="https://images.unsplash.com/photo-1512389098783-66b81f86e199?w=1200&h=300&fit=crop")
        
        # Add Christmas tree icon as thumbnail
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
        
        return embed
        
    def create_order_summary_embed(self, user):
        """Create a beautiful Christmas personal order summary"""
        vn_time = get_vietnam_time()
        embed = discord.Embed(
            title="�✨ ĐƠN HÀNG NOEL CÁ NHÂN ✨🎄",
            description=f"""
╔═══════════════════════════════════╗
║       🎅 GIỎ NOEL CỦA BẠN 🎅       ║
╚═══════════════════════════════════╝

🎅 Ho ho ho, {user.display_name}! Chào mừng bạn đến với bữa tiệc Noel!

🗓️ **Hôm nay:** {vn_time.strftime('%d/%m/%Y')} 
⏰ **Giờ Noel:** {vn_time.strftime('%H:%M:%S')} 
❄️ **Tâm trạng:** Đầy phấn khích và háo hức! 
🎁 *Cảm ơn bạn đã tham gia bữa tiệc Noel cùng chúng tôi!*
""",
            color=0xC41E3A  # Christmas red
        )

        user_id = str(user.id)
        total_items = 0
        order_text = ""
        
        if user_id in self.user_orders:
            for i, (food, qty) in enumerate(self.user_orders[user_id].items(), 1):
                order_text += f"`{i:02d}.` **{food}**\n"
                order_text += f"     └─ Số lượng: `{qty}`\n\n"
                total_items += qty

        if not order_text:
            order_text = "```\n� Chưa có món nào trong giỏ Noel\n```"

        embed.add_field(
            name="📋 **CHI TIẾT ĐƠN NOEL**",
            value=order_text,
            inline=False
        )
        
        # Christmas summary statistics
        summary_text = f"""
� **Tổng số món Noel:** `{total_items}`
📊 **Trạng thái:** {'`🔔 Đã chốt đơn Noel`' if self.is_finalized else '`🎄 Đang chuẩn bị`'}
✨ **Chúc mừng Noel:** `Ho ho ho!`
"""
        
        embed.add_field(
            name="📊 **THỐNG KÊ NOEL**",
            value=summary_text,
            inline=False
        )
        
        embed.set_footer(
            text=f"🎄 Cập nhật: {vn_time.strftime('%d/%m/%Y %H:%M:%S')} • Gordon Meow Meow Christmas Service",
            icon_url=user.avatar.url if user.avatar else None
        )
        
        # Use user avatar as thumbnail
        embed.set_thumbnail(url=user.avatar.url if user.avatar else "https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
        
        # Add Christmas feast image
        embed.set_image(url="https://images.unsplash.com/photo-1576020799627-aeac74d58064?w=800&h=200&fit=crop")
        
        return embed

    def create_finalized_order_embed(self):
        """Create a spectacular Christmas finalized order summary"""
        vn_time = get_vietnam_time()
        embed = discord.Embed(
            title="� **HOÀN TẤT ĐẶT HÀNG NOEL** �",
            description=f"""
� **Ho Ho Ho! Bữa tiệc Noel đã được chuẩn bị hoàn tất!**
📅 **Thời gian hoàn tất:** {vn_time.strftime('%d/%m/%Y lúc %H:%M:%S')}
⚡ **Trạng thái:** `🔔 NOEL ĐÃ SẴN SÀNG` 

🌟 *Chúc mừng Noel! Cảm ơn tất cả mọi người đã tham gia bữa tiệc!* 🎁
""",
            color=0xC41E3A  # Christmas red for excitement
        )
        
        # Individual orders with enhanced styling (without price)
        total_orders = len(self.user_orders)
        for i, (user_id, foods) in enumerate(self.user_orders.items(), 1):
            user = self.context.guild.get_member(int(user_id))
            user_name = user.display_name if user else f"Người dùng {user_id}"
            
            user_order = ""
            user_total = 0
            
            for food, qty in foods.items():
                user_order += f"▸ **{food}**: `{qty}` món\n"
                user_total += qty
            
            user_order += f"\n📊 **Tổng số món:** `{user_total}`"
            
            embed.add_field(
                name=f"👤 **Đơn #{i:02d} - {user_name}**",
                value=user_order,
                inline=True
            )
        
        # Grand total with spectacular display (without price)
        total_items = 0
        food_totals = {}
        
        for foods in self.user_orders.values():
            for food, qty in foods.items():
                total_items += qty
                if food in food_totals:
                    food_totals[food] += qty
                else:
                    food_totals[food] = qty
        
        totals_text = "```diff\n+ TỔNG KẾT CUỐI CÙNG +\n```\n"
        for food, qty in food_totals.items():
            christmas_progress = "🎄" * min(qty, 8) + "❄️" * max(0, 8 - qty)
            totals_text += f"🎁 **{food}**: `{qty}` {christmas_progress}\n"
        
        totals_text += f"\n🏆 **TỔNG CỘNG:** `{total_items}` món Noel"
        totals_text += f"\n🎅 **SỐ NGƯỜI THAM GIA:** `{total_orders}` người"
        totals_text += f"\n🌟 **CHÚC MỪNG NOEL 2025!**"
        
        embed.add_field(
            name="📊 **THỐNG KÊ TỔNG KẾT NOEL**",
            value=totals_text,
            inline=False
        )
        
        embed.set_footer(
            text="� Chúc mừng Noel! Cảm ơn bạn đã sử dụng Gordon Meow Meow Christmas Service! ⭐",
            icon_url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png"
        )
        
        # Add Christmas celebration food image
        embed.set_image(url="https://images.unsplash.com/photo-1512389098783-66b81f86e199?w=1200&h=300&fit=crop")
        
        # Add Christmas success/celebration thumbnail
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2913/2913465.png")
        
        return embed
        return embed