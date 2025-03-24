import discord

class OrderModal(discord.ui.Modal, title="Nhập chi tiết đơn đặt món ăn"):
    def __init__(self, food_name: str, callback):
        super().__init__()
        self.food_name = food_name
        self.callback = callback
        
        self.quantity = discord.ui.TextInput(
            label="Số lượng",
            placeholder="Nhập số lượng món ăn muốn đặt: ",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                await interaction.response.send_message("Sai số lượng, vui lòng nhập số lượng lại!", ephemeral=True)
                return
            await self.callback(interaction, self.food_name, qty)
        except ValueError:
            await interaction.response.send_message("Vui lòng nhập số lượng lại!", ephemeral=True)
