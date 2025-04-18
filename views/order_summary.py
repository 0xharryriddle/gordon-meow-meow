import discord
from views.order_modal import OrderModal

class OrderSummaryView(discord.ui.View):
    def __init__(self, menu_view, interaction):
        super().__init__(timeout=180)
        self.menu_view = menu_view  # Reference to the parent menu view
        self.interaction = interaction  # Store the original interaction
        self.delete_cd_time = menu_view.delete_cd_time
        
        # Get all the user's orders to create the buttons
        self.create_food_buttons()
    
    async def create_food_buttons(self):
        """Create buttons for each food item the user has ordered"""
        try:
            # Get user's database ID
            user_db_id = await self.menu_view.database.get_or_create_user(
                self.interaction.user.id,
                self.interaction.user.display_name
            )
            
            # Get user's items from database
            rows = await self.menu_view.bot.database.connection.execute(
                """
                SELECT i.id, i.name, ui.quantity FROM user_item ui
                JOIN items i ON ui.item_id = i.id
                WHERE ui.user_id = ? AND i.order_id = ?
                ORDER BY i.name
                """,
                (user_db_id, self.menu_view.order_id)
            )
            
            async with rows as cursor:
                results = await cursor.fetchall()
                for row in results:
                    item_id = row[0]
                    food_name = row[1]
                    qty = row[2]
                    
                    # Create a button for each food item
                    edit_button = discord.ui.Button(
                        label=f"Chỉnh sửa {food_name} (x{qty})",
                        style=discord.ButtonStyle.primary,
                        custom_id=f"edit_{food_name}"
                    )
                    edit_button.callback = lambda i=food_name: self.edit_food_callback(i)
                    self.add_item(edit_button)
                    
                    remove_button = discord.ui.Button(
                        label=f"Xóa {food_name}",
                        style=discord.ButtonStyle.danger,
                        custom_id=f"remove_{food_name}"
                    )
                    remove_button.callback = lambda i=food_name: self.remove_food_callback(i)
                    self.add_item(remove_button)
        except Exception as e:
            print(f"Error in create_food_buttons: {e}")
    
    async def edit_food_callback(self, food_name):
        """Callback for editing a food item quantity"""
        try:
            # Don't allow modifications if order is finalized
            if self.menu_view.is_finalized:
                await self.interaction.response.send_message(
                    f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
                
            # Show quantity modal
            modal = OrderModal(food_name, self.menu_view.handle_quantity)
            await self.interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error in edit_food_callback: {e}")
    
    async def remove_food_callback(self, food_name):
        """Callback for removing a food item"""
        try:
            # Don't allow modifications if order is finalized
            if self.menu_view.is_finalized:
                await self.interaction.response.send_message(
                    f"Đơn đã được chốt và không thể thay đổi! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
                
            # Find the item ID for this food
            item_id = await self.menu_view.get_item_id_by_name(food_name)
            
            if item_id:
                # Get user's database ID
                user_db_id = await self.menu_view.database.get_or_create_user(
                    self.interaction.user.id,
                    self.interaction.user.display_name
                )
                
                # Delete the user's item
                await self.menu_view.bot.database.connection.execute(
                    "DELETE FROM user_item WHERE user_id = ? AND item_id = ?",
                    (user_db_id, item_id)
                )
                await self.menu_view.bot.database.connection.commit()
                
                await self.interaction.response.send_message(
                    f"Đã xóa món {food_name}! (Tự động xóa sau {self.delete_cd_time}s)",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                
                # Update the menu
                await self.menu_view.update_public_menu()
                
                # Update the user's order summary
                new_embed = await self.menu_view.create_order_summary_embed(self.interaction.user)
                await self.interaction.followup.edit_message(
                    message_id=self.interaction.message.id,
                    embed=new_embed,
                    view=OrderSummaryView(self.menu_view, self.interaction)  # Create a new view with updated buttons
                )
        except Exception as e:
            print(f"Error in remove_food_callback: {e}")