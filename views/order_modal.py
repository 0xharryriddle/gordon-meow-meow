import discord
from utils import var_global

class OrderModal(discord.ui.Modal, title="� Đặt món Noel"):
    def __init__(self, food_name: str, callback):
        super().__init__()
        self.food_name = food_name
        self.callback = callback
        self.delete_cd_time = var_global.cd_time
        
        # Christmas themed title with food name
        short_name = food_name[:25] + "..." if len(food_name) > 25 else food_name
        self.title = f"🎅 {short_name}"
        
        self.quantity = discord.ui.TextInput(
            label="🎁 Số lượng món Noel",
            placeholder="Nhập số (VD: 1, 2, 3, 4, 5...)",
            min_length=1,
            max_length=3,
            required=True,
            style=discord.TextStyle.short
        )
        self.add_item(self.quantity)
        
        # Add Christmas themed notes field
        self.notes = discord.ui.TextInput(
            label="🎄 Ghi chú Noel (tùy chọn)",
            placeholder="VD: Ít cay, nhiều rau, không hành, thêm gia vị Noel...",
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
                error_embed = discord.Embed(
                    title="❌ **SỐ LƯỢNG KHÔNG HỢP LỆ**",
                    description="""
```diff
- Số lượng phải lớn hơn 0!
```

💡 **Vui lòng nhập số dương** (VD: 1, 2, 3...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
                    color=0xE74C3C
                )
                error_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4539/4539910.png")
                await interaction.response.send_message(
                    embed=error_embed,
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            if qty > 99:
                error_embed = discord.Embed(
                    title="⚠️ **SỐ LƯỢNG QUÁ LỚN**",
                    description="""
```diff
- Số lượng tối đa là 99!
```

💡 **Vui lòng nhập số nhỏ hơn 100**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
                    color=0xF39C12
                )
                error_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3064/3064197.png")
                await interaction.response.send_message(
                    embed=error_embed,
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
                
            await self.callback(interaction, self.food_name, qty)
            
        except ValueError:
            error_embed = discord.Embed(
                title="❌ **ĐỊNH DẠNG SAI**",
                description="""
```ansi
\u001b[1;31m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
   ⚠️ **CHỈ NHẬP SỐ!**
\u001b[1;31m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
```

💡 **Vui lòng chỉ nhập số nguyên**
✅ Đúng: `1`, `2`, `5`, `10`
❌ Sai: `một`, `1.5`, `abc`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
                color=0xE74C3C
            )
            error_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/463/463612.png")
            await interaction.response.send_message(
                embed=error_embed,
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
