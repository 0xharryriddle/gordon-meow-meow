import discord
import datetime
from utils import var_global

class FinalizedOrderView(discord.ui.View):
    """Enhanced finalized order view with premium features"""
    
    def __init__(self, menu_view):
        super().__init__(timeout=3600)
        self.menu_view = menu_view
        self.delete_cd_time = var_global.cd_time
        
        # Enhanced copy button
        copy_button = discord.ui.Button(
            label="Sao chép tổng kết",
            style=discord.ButtonStyle.success,
            custom_id="copy_summary",
            emoji="📋"
        )
        copy_button.callback = self.copy_summary_callback
        self.add_item(copy_button)
        
        # Add print-friendly format button
        print_button = discord.ui.Button(
            label="Định dạng in ấn",
            style=discord.ButtonStyle.secondary,
            custom_id="print_format",
            emoji="🖨️"
        )
        print_button.callback = self.print_format_callback
        self.add_item(print_button)
        
        # Add reopen order button
        reopen_button = discord.ui.Button(
            label="Mở lại đơn hàng",
            style=discord.ButtonStyle.primary,
            custom_id="reopen_order",
            emoji="🔓"
        )
        reopen_button.callback = self.reopen_order_callback
        self.add_item(reopen_button)
        
        # Add export button (mock)
        export_button = discord.ui.Button(
            label="Xuất Excel",
            style=discord.ButtonStyle.secondary,
            custom_id="export_excel",
            emoji="📊"
        )
        export_button.callback = self.export_callback
        self.add_item(export_button)
    
    async def reopen_order_callback(self, interaction: discord.Interaction):
        """Handle reopen order button click"""
        try:
            # Check if user has permissions
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ **Quyền hạn không đủ!** Chỉ admin mới có thể mở lại đơn hàng.",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Check if order is already open
            if not self.menu_view.is_finalized:
                await interaction.response.send_message(
                    "ℹ️ **Đơn hàng đã mở rồi!**",
                    ephemeral=True,
                    delete_after=self.delete_cd_time
                )
                return
            
            # Reopen the order
            self.menu_view.is_finalized = False
            
            # Re-enable the dropdown and buttons in the main menu
            self.menu_view.food_select.disabled = False
            for item in self.menu_view.children:
                if hasattr(item, 'custom_id'):
                    if item.custom_id in ["clear_all_order", "finalize_order"]:
                        item.disabled = False
                    elif item.custom_id == "unfinalize_order":
                        item.disabled = True
            
            # Update the main menu
            await self.menu_view.update_public_menu()
            
            # Create success embed for temporary notification
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
            
            # Send temporary success message (will auto-delete)
            await interaction.response.send_message(
                embed=success_embed,
                ephemeral=False,
                delete_after=self.delete_cd_time * 3
            )
            
            # Delete the finalized order message to clean up UI
            try:
                await interaction.message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                print("Warning: Bot doesn't have permission to delete the finalized order message")
            except Exception as e:
                print(f"Error deleting finalized order message: {e}")
            
        except Exception as e:
            print(f"Error in reopen_order_callback: {e}")
            await interaction.response.send_message(
                "❌ **Lỗi!** Không thể mở lại đơn hàng. Vui lòng thử lại sau.",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )

    async def copy_summary_callback(self, interaction: discord.Interaction):
        """Enhanced copy functionality with beautiful formatting"""
        try:
            copy_text = self.menu_view.generate_copy_text()
            
            # Enhanced copy format without pricing
            enhanced_copy = f"""
🎉 **TỔNG KẾT ĐƠN HÀNG** 🎉
📅 Ngày: {datetime.datetime.now().strftime('%d/%m/%Y')}
⏰ Thời gian: {datetime.datetime.now().strftime('%H:%M:%S')}

{copy_text}

✨ Được tạo bởi Gordon Meow Meow Service ✨
"""
            
            await interaction.response.send_message(
                f"📋 **Dữ liệu đã sẵn sàng để sao chép:**\n```\n{enhanced_copy}\n```\n\n💡 *Tip: Chọn toàn bộ text trong khung và nhấn Ctrl+C*",
                ephemeral=True,
                delete_after=self.delete_cd_time * 40
            )
            
        except Exception as e:
            print(f"Error in copy_summary_callback: {e}")
            await interaction.response.send_message(
                "❌ **Lỗi!** Không thể tạo bản sao. Vui lòng thử lại sau.",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
    
    async def print_format_callback(self, interaction: discord.Interaction):
        """Create print-friendly format"""
        try:
            print_text = f"""
{"="*50}
           ĐƠN HÀNG THỰC PHẨM
{"="*50}
Ngày: {datetime.datetime.now().strftime('%d/%m/%Y')}
Giờ:  {datetime.datetime.now().strftime('%H:%M:%S')}

{self.menu_view.generate_copy_text()}

{"="*50}
Cảm ơn quý khách!
Gordon Meow Meow Service
{"="*50}
"""
            
            await interaction.response.send_message(
                f"🖨️ **Định dạng in ấn:**\n```\n{print_text}\n```",
                ephemeral=True,
                delete_after=self.delete_cd_time * 40
            )
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ Lỗi tạo định dạng in ấn!",
                ephemeral=True,
                delete_after=self.delete_cd_time
            )
    
    async def export_callback(self, interaction: discord.Interaction):
        """Mock export functionality (for demonstration)"""
        await interaction.response.send_message(
            "📊 **Xuất Excel:** Tính năng này đang được phát triển! 🚀\n\n📋 Hiện tại hãy sử dụng nút **Sao chép tổng kết** để lấy dữ liệu.",
            ephemeral=True,
            delete_after=self.delete_cd_time * 3
        )
