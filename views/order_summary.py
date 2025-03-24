import discord
from views.order_modal import OrderModal

class OrderSummaryView(discord.ui.View):
    """A view for the private order summary that allows modification"""
    def __init__(self, menu_view, interaction):
        super().__init__(timeout=180)
        self.menu_view = menu_view
        self.interaction = interaction
        self.user_id = str(interaction.user.id)
        
        # Create dropdown for selecting items to edit/remove
        self.create_item_select()
        
        # Add Edit Item button
        edit_button = discord.ui.Button(
            label="Sửa món",
            style=discord.ButtonStyle.primary,
            custom_id="edit_item",
            emoji="✏️"
        )
        edit_button.callback = self.edit_item_callback
        self.add_item(edit_button)
        
        # Add Remove Item button
        remove_button = discord.ui.Button(
            label="Xóa món",
            style=discord.ButtonStyle.danger,
            custom_id="remove_item",
            emoji="❌"
        )
        remove_button.callback = self.remove_item_callback
        self.add_item(remove_button)
        
    def create_item_select(self):
        """Create a dropdown with current order items"""
        # Only add if there are items in the order
        if self.user_id in self.menu_view.user_orders and self.menu_view.user_orders[self.user_id]:
            options = [
                discord.SelectOption(
                    label=food[:25],
                    value=food,
                    description=f"Số lượng: {qty}"
                ) for food, qty in self.menu_view.user_orders[self.user_id].items()
            ]
            
            # Add the select menu for items
            self.item_select = discord.ui.Select(
                placeholder="Chọn món để sửa/xóa",
                options=options,
                custom_id="item_select"
            )
            # Set the callback
            self.item_select.callback = self.on_item_select
            self.add_item(self.item_select)
            
    async def on_item_select(self, interaction: discord.Interaction):
        """Handle when an item is selected from the dropdown"""
        # Just acknowledge the selection
        await interaction.response.defer()
    
    async def edit_item_callback(self, interaction: discord.Interaction):
        """Handle editing an item's quantity"""
        if not hasattr(self, 'item_select'):
            await interaction.response.send_message(
                "Không có món nào để sửa!",
                ephemeral=True
            )
            return
            
        if not self.item_select.values:
            await interaction.response.send_message(
                "Vui lòng chọn một món từ danh sách trước!",
                ephemeral=True
            )
            return
            
        selected_food = self.item_select.values[0]
        # Use the OrderModal to get new quantity
        modal = OrderModal(selected_food, self.handle_edit_quantity)
        await interaction.response.send_modal(modal)
        
    async def handle_edit_quantity(self, interaction: discord.Interaction, food_name: str, quantity: int):
        """Handle the quantity update from the modal"""
        # Update the quantity
        self.menu_view.user_orders[self.user_id][food_name] = quantity
        
        # Update the order summary
        embed = self.menu_view.create_order_summary_embed(interaction.user)
        new_view = OrderSummaryView(self.menu_view, interaction)
        
        # Update public menu
        await self.menu_view.update_public_menu()
        
        await interaction.response.edit_message(
            embed=embed,
            view=new_view
        )
        
    async def remove_item_callback(self, interaction: discord.Interaction):
        """Handle removing an item from the order"""
        if not hasattr(self, 'item_select'):
            await interaction.response.send_message(
                "Không có món nào để xóa!",
                ephemeral=True
            )
            return
            
        if not self.item_select.values:
            await interaction.response.send_message(
                "Vui lòng chọn một món từ danh sách trước!",
                ephemeral=True
            )
            return
            
        selected_food = self.item_select.values[0]
        
        # Remove the item
        if selected_food in self.menu_view.user_orders[self.user_id]:
            del self.menu_view.user_orders[self.user_id][selected_food]

        # Update the order summary
        if self.user_id not in self.menu_view.user_orders or not self.menu_view.user_orders[self.user_id]:
            # Update view with empty order
            # await interaction.message.edit(view=None)
            # If order is now empty
            await interaction.response.send_message(
                "Đơn hàng của bạn hiện đang trống. Thêm món sử dụng menu chính.",
                ephemeral=True
            )
        else:
            # Update with remaining items
            embed = self.menu_view.create_order_summary_embed(interaction.user)
            new_view = OrderSummaryView(self.menu_view, interaction)
            
            await interaction.response.edit_message(
                embed=embed,
                view=new_view
            )
        
        # Update public menu
        await self.menu_view.update_public_menu()

        # If no more items, remove the user entry
        if not self.menu_view.user_orders[self.user_id]:
            del self.menu_view.user_orders[self.user_id]
            
            
