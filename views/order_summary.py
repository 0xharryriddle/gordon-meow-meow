import discord
from views.order_modal import OrderModal
from utils import var_global

class OrderSummaryView(discord.ui.View):
    """Enhanced order summary view with stunning UI"""
    def __init__(self, menu_view, interaction):
        super().__init__(timeout=None)
        self.menu_view = menu_view
        self.interaction = interaction
        self.user_id = str(interaction.user.id)
        self.delete_cd_time = var_global.cd_time
        
        # Create enhanced dropdown
        self.create_item_select()
        
        # Enhanced buttons with better styling
        edit_button = discord.ui.Button(
            label="Chỉnh sửa món",
            style=discord.ButtonStyle.primary,
            custom_id="edit_item",
            emoji="✏️",
            row=1
        )
        edit_button.callback = self.edit_item_callback
        self.add_item(edit_button)
        
        remove_button = discord.ui.Button(
            label="Xóa món",
            style=discord.ButtonStyle.danger,
            custom_id="remove_item",
            emoji="🗑️",
            row=1
        )
        remove_button.callback = self.remove_item_callback
        self.add_item(remove_button)
        
        # Add quick actions
        clear_all_button = discord.ui.Button(
            label="Xóa tất cả",
            style=discord.ButtonStyle.secondary,
            custom_id="clear_all",
            emoji="🧹",
            row=1
        )
        clear_all_button.callback = self.clear_all_callback
        self.add_item(clear_all_button)
        
    def create_item_select(self):
        """Create enhanced dropdown with better visual indicators"""
        if self.user_id in self.menu_view.user_orders and self.menu_view.user_orders[self.user_id]:
            options = []
            for food, qty in self.menu_view.user_orders[self.user_id].items():
                # Add emoji based on food type
                if "cơm" in food.lower():
                    emoji = "🍚"
                elif any(x in food.lower() for x in ["bún", "phở", "miến"]):
                    emoji = "🍜"
                elif "thịt" in food.lower():
                    emoji = "🥩"
                elif "cá" in food.lower():
                    emoji = "🐟"
                elif "canh" in food.lower():
                    emoji = "🍲"
                else:
                    emoji = "🍽️"
                
                options.append(discord.SelectOption(
                    label=f"{food[:20]}..." if len(food) > 20 else food,
                    value=food,
                    description=f"Số lượng: {qty} | Chọn để chỉnh sửa",
                    emoji=emoji
                ))
            
            self.item_select = discord.ui.Select(
                placeholder="🎯 Chọn món để thao tác...",
                options=options,
                custom_id="item_select"
            )
            self.item_select.callback = self.on_item_select
            self.add_item(self.item_select)
    
    async def clear_all_callback(self, interaction: discord.Interaction):
        """Clear all items with confirmation"""
        if self.user_id in self.menu_view.user_orders:
            self.menu_view.user_orders[self.user_id].clear()
            del self.menu_view.user_orders[self.user_id]
        
        await self.menu_view.update_public_menu()
        
        await interaction.response.send_message(
            "🧹 **Đã xóa tất cả món ăn!** Bạn có thể đặt lại từ menu chính.",
            ephemeral=True,
            delete_after=self.delete_cd_time
        )

    async def on_item_select(self, interaction: discord.Interaction):
        """Handle when an item is selected from the dropdown"""
        # Just acknowledge the selection
        await interaction.response.defer()
    
    async def edit_item_callback(self, interaction: discord.Interaction):
        """Handle editing an item's quantity"""
        if not hasattr(self, 'item_select'):
            await interaction.response.send_message(
                "Không có món nào để sửa!",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        if not self.item_select.values:
            await interaction.response.send_message(
                "Vui lòng chọn một món từ danh sách trước!",
                ephemeral=True,
                delete_after=self.delete_cd_time
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
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        if not self.item_select.values:
            await interaction.response.send_message(
                "Vui lòng chọn một món từ danh sách trước!",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
            return
            
        selected_food = self.item_select.values[0]
        
        # Remove the item
        if selected_food in self.menu_view.user_orders[self.user_id]:
            del self.menu_view.user_orders[self.user_id][selected_food]

        # Update the order summary
        if self.user_id not in self.menu_view.user_orders or not self.menu_view.user_orders[self.user_id]:
            await interaction.response.send_message(
                "Đơn hàng của bạn hiện đang trống. Thêm món sử dụng menu chính. (Tự động xóa sau 3 giây)",
                ephemeral=True,
                delete_after=self.delete_cd_time
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


