import datetime
import discord
from discord.ext.commands import Context
from views.order_modal import OrderModal
from views.order_summary import OrderSummaryView
from utils import var_global

class MenuView(discord.ui.View):
    def __init__(self, menu: list, context: Context, message_id=None):
        super().__init__(timeout=21600)  # 6 hours: 6 * 60 * 60
        self.menu = menu
        self.context = context
        self.user_orders = {}  # Dict to store orders by user: {user_id: {food_name: quantity}}
        self.message_id = message_id  # Store message ID for updating the embed
        self.message = None  # Will store the message object
        self.order_message = None  # Will store the user's private order message
        self.is_finalized = False  # Track if the order has been finalized
        self.delete_cd_time = var_global.cd_time
        
        # Store this view as the active one in the bot
        if hasattr(context.bot, 'active_order_view'):
            context.bot.active_order_view = self
        
        # Create dropdown menu for food selection
        self.food_select = discord.ui.Select(
            placeholder="Chọn món ăn",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label=food[:25],  # Discord has a 25-character limit for select options
                    value=food,
                    description=f"Order {food}",
                    emoji="🍽️"  # Food emoji
                ) for food in menu
            ]
        )
        self.food_select.callback = self.food_select_callback
        self.add_item(self.food_select)
        
        # Add clear all order button
        clear_all_button = discord.ui.Button(
            label="Xóa tất cả món ăn",
            style=discord.ButtonStyle.danger,
            custom_id="clear_all_order",
            emoji="🗑️"  # Trash emoji
        )
        clear_all_button.callback = self.clear_all_order_callback
        self.add_item(clear_all_button)
        
        # Add view order button
        view_button = discord.ui.Button(
            label="Xem món ăn đã đặt",
            style=discord.ButtonStyle.primary,
            custom_id="view_order",
            emoji="👀"  # Eyes emoji
        )
        view_button.callback = self.view_order_callback
        self.add_item(view_button)
        
        finalize_button = discord.ui.Button(
                label="Chốt tất cả món ăn",
                style=discord.ButtonStyle.success,
                custom_id="finalize_order",
                emoji="🔒"  # Lock emoji
            )
        finalize_button.callback = self.finalize_order_callback
        self.add_item(finalize_button)

        unfinalize_button  = discord.ui.Button(
            label="Mở lại đơn",
            style=discord.ButtonStyle.secondary,
            custom_id="unfinalize_order",
            emoji="🔓"  # Unlock emoji
        )
        unfinalize_button.callback = self.unfinalize_order_callback
        self.add_item(unfinalize_button)

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
    
    async def finalize_order_callback(self, interaction: discord.Interaction):
        """Callback for finalizing all orders"""
            
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
        
        # Send the finalized order to the channel
        await interaction.response.send_message(
            f"Tất cả đơn đã được chốt! (Tự động xóa sau {self.delete_cd_time} giây)",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )
        
        await interaction.channel.send(embed=embed)
    
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
        
        # Enable dropdown
        self.food_select.disabled = False

        await self.update_public_menu()
        
        await interaction.response.send_message(
            f"Đơn đã được mở lại! (Tự động xóa sau {self.delete_cd_time} giây)",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )

    async def disable_ordering(self):
        """Disable ordering functionality after finalization"""
        # Disable dropdown
        self.food_select.disabled = True
        
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
        """Create a beautiful menu embed that everyone can see, including orders"""
        embed = discord.Embed(
            title="#📋 Thực đơn hôm nay",
            description=f"## **Ngày:** {datetime.datetime.now().strftime('%d/%m/%Y')}",
            color=0x2ecc71  # Nice green color
        )
        
        # Add menu items section with emoji
        menu_text = ""
        for i, item in enumerate(self.menu, 1):
            menu_text += f"**{i}.** {item}\n"
        
        embed.add_field(name="🍽️ Món ăn có sẵn", value=menu_text, inline=False)
        
        # Add current orders section if there are any
        if self.user_orders:
            orders_text = ""
            total_by_food = {}  # Track totals by food item
            
            # Group by food item
            for user_id, foods in self.user_orders.items():
                user = self.context.guild.get_member(int(user_id))
                user_name = user.display_name if user else "Người dùng không xác định"
                
                for food, qty in foods.items():
                    # Add to total count for this food
                    if food in total_by_food:
                        total_by_food[food] += qty
                    else:
                        total_by_food[food] = qty
                        
                    # Add to user-specific order list
                    orders_text += f"• **{food}** (x{qty}) - Đặt bởi {user_name}\n"
            
            # Add order summary
            if orders_text:
                embed.add_field(name="🛒 Các món đã đặt", value=orders_text, inline=False)
                
                # Add totals by food item
                totals_text = ""
                for food, total in total_by_food.items():
                    totals_text += f"• **{food}**: {total}\n"
                
                embed.add_field(name="📊 Tổng món đã đặt", value=totals_text, inline=False)
        
        # Add status section
        status_text = "Đang mở đơn - sử dụng các nút bên dưới để đặt món"
        if self.is_finalized:
            status_text = "Đơn đã được chốt và không thể thay đổi"
            
        embed.add_field(name="📝 Trạng thái", value=status_text, inline=False)
        
        # Add footer
        footer_text = "Sử dụng các nút bên dưới để đặt món • Gordon Meow Meow Service"
        if self.is_finalized:
            footer_text = "Đơn đã chốt • Gordon Meow Meow Service"
            
        embed.set_footer(text=footer_text)
        
        return embed
        
    def create_order_summary_embed(self, user):
        """Create a private order summary embed for the user"""
        embed = discord.Embed(
            title="🛒 Món bạn đã đặt",
            description=f"**Đặt bởi:** {user.mention}",
            color=0x3498db  # Nice blue color
        )

        user_id = str(user.id)
        total_items = 0
        order_text = ""
        
        if user_id in self.user_orders:
            for food, qty in self.user_orders[user_id].items():
                order_text += f"• **{food}**: {qty}\n"
                total_items += qty

        embed.add_field(name="📋 Chi tiết đơn", value=order_text if order_text else "*No items in order*", inline=False)
        embed.add_field(name="📊 Tổng số lượng món đã đặt", value=str(total_items), inline=True)
        
        footer_text = f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')} • Dùng các nút bên dưới để tương tác"
        if self.is_finalized:
            footer_text = f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')} • Orders finalized"
            
        embed.set_footer(text=footer_text)
        
        # Add a nice thumbnail
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1046/1046747.png")
        
        return embed
    
    def create_finalized_order_embed(self):
        """Create a finalized order summary for all orders"""
        embed = discord.Embed(
            title="🔒 Tổng kết cuối cùng",
            description=f"**Ngày đặt món:** {datetime.datetime.now().strftime('%d/%m/%Y lúc %H:%M:%S')}",
            color=0xe74c3c  # Red color for finality
        )
        
        # Add individual orders
        for user_id, foods in self.user_orders.items():
            user = self.context.guild.get_member(int(user_id))
            user_name = user.display_name if user else f"Người dùng {user_id}"
            
            user_order = ""
            user_total = 0
            
            for food, qty in foods.items():
                user_order += f"• {food}: {qty}\n"
                user_total += qty
                
            user_order += f"\nTổng số món: {user_total}"
            
            embed.add_field(
                name=f"📝 Đơn đặt món của {user_name}",
                value=user_order,
                inline=True
            )
        
        # Add grand total section
        total_items = 0
        food_totals = {}
        
        for foods in self.user_orders.values():
            for food, qty in foods.items():
                total_items += qty
                if food in food_totals:
                    food_totals[food] += qty
                else:
                    food_totals[food] = qty
        
        totals_text = ""
        for food, qty in food_totals.items():
            totals_text += f"• **{food}**: {qty}\n"
            
        totals_text += f"\n**Tổng cộng**: {total_items} món"
        
        embed.add_field(
            name="📊 Tổng kết số lượng",
            value=totals_text,
            inline=False
        )
        
        embed.set_footer(text="Đơn đã được chốt • Gordon Meow Meow Service")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3183/3183463.png")  # Receipt icon
        
        return embed