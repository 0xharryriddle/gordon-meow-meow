import datetime
import discord
from discord.ext.commands import Context
from views.order_modal import OrderModal
from views.order_summary import OrderSummaryView
from utils import var_global

class MenuView(discord.ui.View):
    def __init__(self, menu: list, context: Context, message_id=None):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.menu = menu
        self.context = context
        self.bot = context.bot  # Store reference to bot for accessing database
        self.database = context.bot.database  # Get database manager
        self.message_id = message_id  # Store message ID for updating the embed
        self.message = None  # Will store the message object
        self.order_message = None  # Will store the user's private order message
        self.is_finalized = False  # Track if the order has been finalized
        self.delete_cd_time = var_global.cd_time
        self.order_id = None  # Will store the database order ID
        
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

    async def initialize_order(self):
        """Initialize the order in the database when the menu is first created"""
        try:
            # Get the message ID once the message is sent
            if self.message and not self.order_id:
                # Get or create user
                user_db_id = await self.database.get_or_create_user(
                    self.context.author.id, 
                    self.context.author.display_name
                )
                
                # Create the order
                self.order_id = await self.database.create_order(
                    user_db_id,
                    str(self.context.guild.id),
                    str(self.message.id)
                )
                
                # Create items for each menu option
                for food in self.menu:
                    await self.database.create_item(self.order_id, food)
        except Exception as e:
            print(f"Error in initialize_order: {e}")

    async def food_select_callback(self, interaction: discord.Interaction):
        try:
            # Don't allow modifications if order is finalized
            if self.is_finalized:
                await interaction.response.send_message(
                    f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Initialize order if not already done
            if not self.order_id:
                await self.initialize_order()
                
            selected_food = self.food_select.values[0]
            modal = OrderModal(selected_food, self.handle_quantity)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error in food_select_callback: {e}")

    async def handle_quantity(self, interaction: discord.Interaction, food_name: str, quantity: int):
        try:
            # Don't allow modifications if order is finalized
            if self.is_finalized:
                await interaction.response.send_message(
                    f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Get user's database ID
            user_db_id = await self.database.get_or_create_user(
                interaction.user.id,
                interaction.user.display_name
            )
            
            # Find the item ID for this food
            item_id = await self.get_item_id_by_name(food_name)
            
            if item_id:
                # Add or update the user's order for this item
                await self.database.add_user_item(user_db_id, item_id, quantity)
                
                # Update the public menu to show the new order
                await self.update_public_menu()

                await interaction.response.send_message(
                    content=f"Đã chọn món ăn thành công! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
            else:
                await interaction.response.send_message(
                    content=f"Không tìm thấy món ăn này! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
        except Exception as e:
            print(f"Error in handle_quantity: {e}")

    async def get_item_id_by_name(self, food_name: str) -> int:
        """Get the database item ID for a food name"""
        try:
            rows = await self.bot.database.connection.execute(
                "SELECT id FROM items WHERE order_id = ? AND name = ?",
                (self.order_id, food_name)
            )
            async with rows as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error in get_item_id_by_name: {e}")
            return None

    async def clear_order_callback(self, interaction: discord.Interaction, food_name: str, qty: int):
        try:
            if self.is_finalized:
                await interaction.response.send_message(
                    f"Thực đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Get user's database ID
            user_db_id = await self.database.get_or_create_user(
                interaction.user.id,
                interaction.user.display_name
            )
            
            # Find the item ID for this food
            item_id = await self.get_item_id_by_name(food_name)
            
            if item_id:
                # Update the quantity (if qty is 0, the item will be removed in add_user_item)
                await self.database.add_user_item(user_db_id, item_id, qty)
                
                await interaction.response.send_message(
                    f"Món ăn của bạn đã được xóa! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                # Update the public menu
                await self.update_public_menu()
        except Exception as e:
            print(f"Error in clear_order_callback: {e}")

    async def clear_all_order_callback(self, interaction: discord.Interaction):
        try:
            # Don't allow modifications if order is finalized
            if self.is_finalized:
                await interaction.response.send_message(
                    f"Thực đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Get user's database ID
            user_db_id = await self.database.get_or_create_user(
                interaction.user.id,
                interaction.user.display_name
            )
            
            # Delete all user's items
            await self.bot.database.connection.execute(
                """
                DELETE FROM user_item 
                WHERE user_id = ? AND item_id IN (
                    SELECT id FROM items WHERE order_id = ?
                )
                """,
                (user_db_id, self.order_id)
            )
            await self.bot.database.connection.commit()
            
            await interaction.response.send_message(
                f"Tất cả món ăn của bạn đã được xóa! (Tự động xóa sau {self.delete_cd_time} giây)",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            
            # Update the public menu
            await self.update_public_menu()
        except Exception as e:
            print(f"Error in clear_all_order_callback: {e}")

    async def view_order_callback(self, interaction: discord.Interaction):
        try:
            # Get user's database ID
            user_db_id = await self.database.get_or_create_user(
                interaction.user.id,
                interaction.user.display_name
            )
            
            # Check if user has any items
            rows = await self.bot.database.connection.execute(
                """
                SELECT COUNT(*) FROM user_item ui
                JOIN items i ON ui.item_id = i.id
                WHERE ui.user_id = ? AND i.order_id = ?
                """,
                (user_db_id, self.order_id)
            )
            async with rows as cursor:
                result = await cursor.fetchone()
                if not result or result[0] == 0:
                    await interaction.response.send_message(
                        f"Bạn chưa đặt món ăn nào! (Tự động xóa sau {self.delete_cd_time}s)",
                        ephemeral=True,
                        delete_after=self.delete_cd_time
                    )
                    return
                
            # Create order summary embed
            embed = await self.create_order_summary_embed(interaction.user)
            
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
        except Exception as e:
            print(f"Error in view_order_callback: {e}")
    
    async def finalize_order_callback(self, interaction: discord.Interaction):
        """Callback for finalizing all orders"""
        try:
            # Check if there are any orders
            rows = await self.bot.database.connection.execute(
                """
                SELECT COUNT(*) FROM user_item ui
                JOIN items i ON ui.item_id = i.id
                WHERE i.order_id = ?
                """,
                (self.order_id,)
            )
            async with rows as cursor:
                result = await cursor.fetchone()
                if not result or result[0] == 0:
                    await interaction.response.send_message(
                        f"Không có đơn nào để chốt! (Tự động xóa sau {self.delete_cd_time} giây)",
                        ephemeral=True,
                        delete_after=self.delete_cd_time
                    )
                    return
                
            # Update order status to completed
            await self.database.update_order_status(self.order_id, 'completed')
            
            # Create finalized order embed
            embed = await self.create_finalized_order_embed()
            
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
        except Exception as e:
            print(f"Error in finalize_order_callback: {e}")
    
    async def unfinalize_order_callback(self, interaction: discord.Interaction):
        """Callback for re-opening all orders"""
        try:
            # Check if the order is already open
            if not self.is_finalized:
                await interaction.response.send_message(
                    f"Đơn đã mở rồi! (Tự động xóa sau {self.delete_cd_time} giây)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Update order status to pending
            await self.database.update_order_status(self.order_id, 'pending')
            
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
        except Exception as e:
            print(f"Error in unfinalize_order_callback: {e}")

    async def disable_ordering(self):
        """Disable ordering functionality after finalization"""
        try:
            # Disable dropdown
            self.food_select.disabled = True
            
            # Create a new embed indicating orders are finalized
            embed = discord.Embed(
                # @note - Testing purpose
                title="#📋 Thực đơn hôm nay (Testing) - ĐÃ CHỐT ĐƠN ",
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
        except Exception as e:
            print(f"Error in disable_ordering: {e}")

    async def update_public_menu(self):
        """Update the public menu message with current orders"""
        try:
            if self.message:
                embed = await self.create_menu_embed()
                await self.message.edit(embed=embed, view=self)
        except Exception as e:
            print(f"Error in update_public_menu: {e}")

    async def create_menu_embed(self):
        """Create a beautiful menu embed that everyone can see, including orders"""
        try:
            embed = discord.Embed(
                # @note - Testing purpose
                title="#📋 Thực đơn hôm nay (Testing)",
                description=f"## **Ngày:** {datetime.datetime.now().strftime('%d/%m/%Y')}",
                color=0x2ecc71  # Nice green color
            )
            
            # Add menu items section with emoji
            menu_text = ""
            for i, item in enumerate(self.menu, 1):
                menu_text += f"**{i}.** {item}\n"
            
            embed.add_field(name="🍽️ Món ăn có sẵn", value=menu_text, inline=False)
            
            # Fetch orders from database and add them to embed
            if self.order_id:
                rows = await self.bot.database.connection.execute(
                    """
                    SELECT i.name, ui.quantity, u.discord_id, u.username 
                    FROM user_item ui
                    JOIN items i ON ui.item_id = i.id
                    JOIN users u ON ui.user_id = u.id
                    WHERE i.order_id = ?
                    """,
                    (self.order_id,)
                )
                
                orders_text = ""
                total_by_food = {}
                
                async with rows as cursor:
                    results = await cursor.fetchall()
                    
                    if results:
                        for row in results:
                            food_name = row[0]
                            qty = row[1]
                            discord_id = row[2]
                            username = row[3]
                            
                            # Add to total count for this food
                            if food_name in total_by_food:
                                total_by_food[food_name] += qty
                            else:
                                total_by_food[food_name] = qty
                                
                            # Get display name if possible
                            user = self.context.guild.get_member(int(discord_id))
                            display_name = user.display_name if user else username
                            
                            # Add to user-specific order list
                            orders_text += f"• **{food_name}** (x{qty}) - Đặt bởi {display_name}\n"
                
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
        except Exception as e:
            print(f"Error in create_menu_embed: {e}")
            return None
        
    async def create_order_summary_embed(self, user):
        """Create a private order summary embed for the user"""
        try:
            embed = discord.Embed(
                title="🛒 Món bạn đã đặt",
                description=f"**Đặt bởi:** {user.mention}",
                color=0x3498db  # Nice blue color
            )

            # Get user's database ID
            user_db_id = await self.database.get_or_create_user(
                user.id,
                user.display_name
            )
            
            # Get user's items from database
            rows = await self.bot.database.connection.execute(
                """
                SELECT i.name, ui.quantity FROM user_item ui
                JOIN items i ON ui.item_id = i.id
                WHERE ui.user_id = ? AND i.order_id = ?
                """,
                (user_db_id, self.order_id)
            )
            
            total_items = 0
            order_text = ""
            
            async with rows as cursor:
                results = await cursor.fetchall()
                for row in results:
                    food_name = row[0]
                    qty = row[1]
                    order_text += f"• **{food_name}**: {qty}\n"
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
        except Exception as e:
            print(f"Error in create_order_summary_embed: {e}")
            return None
    
    async def create_finalized_order_embed(self):
        """Create a finalized order summary for all orders"""
        try:
            embed = discord.Embed(
                title="🔒 Tổng kết cuối cùng",
                description=f"**Ngày đặt món:** {datetime.datetime.now().strftime('%d/%m/%Y lúc %H:%M:%S')}",
                color=0xe74c3c  # Red color for finality
            )
            
            # Get all orders with user details
            rows = await self.bot.database.connection.execute(
                """
                SELECT u.discord_id, u.username, i.name, ui.quantity
                FROM user_item ui
                JOIN items i ON ui.item_id = i.id
                JOIN users u ON ui.user_id = u.id
                WHERE i.order_id = ?
                ORDER BY u.username, i.name
                """,
                (self.order_id,)
            )
            
            # Group by user
            user_orders = {}
            food_totals = {}
            total_items = 0
            
            async with rows as cursor:
                results = await cursor.fetchall()
                for row in results:
                    discord_id = row[0]
                    username = row[1]
                    food_name = row[2]
                    qty = row[3]
                    
                    # Add to user orders
                    if discord_id not in user_orders:
                        user_orders[discord_id] = {"username": username, "orders": {}}
                    
                    user_orders[discord_id]["orders"][food_name] = qty
                    
                    # Add to food totals
                    if food_name in food_totals:
                        food_totals[food_name] += qty
                    else:
                        food_totals[food_name] = qty
                    
                    total_items += qty
            
            # Add individual orders
            for discord_id, data in user_orders.items():
                username = data["username"]
                orders = data["orders"]
                
                user = self.context.guild.get_member(int(discord_id))
                display_name = user.display_name if user else f"Người dùng {discord_id}"
                
                user_order = ""
                user_total = 0
                
                for food, qty in orders.items():
                    user_order += f"• {food}: {qty}\n"
                    user_total += qty
                    
                user_order += f"\nTổng số món: {user_total}"
                
                embed.add_field(
                    name=f"📝 Đơn đặt món của {display_name}",
                    value=user_order,
                    inline=True
                )
            
            # Add grand total section
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
        except Exception as e:
            print(f"Error in create_finalized_order_embed: {e}")
            return None