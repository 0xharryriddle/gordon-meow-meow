import discord
from utils import var_global

class OrderModal(discord.ui.Modal, title="🍽️ Đặt món ăn"):
    def __init__(self, food_name: str, callback):
        super().__init__()
        self.food_name = food_name
        self.callback = callback
        self.delete_cd_time = var_global.cd_time
        
        # Enhanced title with food name
        self.title = f"🍽️ Đặt món: {food_name[:30]}..."
        
        self.quantity = discord.ui.TextInput(
            label="Số lượng món ăn",
            placeholder="Nhập số lượng (VD: 1, 2, 3...)",
            min_length=1,
            max_length=3,
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.quantity)
        
        # Add notes field for enhanced UX
        self.notes = discord.ui.TextInput(
            label="Ghi chú (tùy chọn)",
            placeholder="VD: Ít cay, nhiều rau, không hành...",
            min_length=0,
            max_length=100,
            required=False,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                await interaction.response.send_message(
                    "❌ **Số lượng không hợp lệ!** Vui lòng nhập số lớn hơn 0.",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            if qty > 99:
                await interaction.response.send_message(
                    "⚠️ **Số lượng quá lớn!** Vui lòng nhập số nhỏ hơn 100.",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
                
            await self.callback(interaction, self.food_name, qty)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ **Định dạng không đúng!** Vui lòng chỉ nhập số (VD: 1, 2, 3...).",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
