# 🎨 Gordon Meow Meow - Visual Style Guide

## 📐 Design System

### 🌈 Color Palette

#### Primary Colors

```python
SUCCESS_GREEN = 0x00D4AA    # ✅ Success states, confirmations
ERROR_RED = 0xE74C3C        # ❌ Errors, deletions
WARNING_ORANGE = 0xF39C12   # ⚠️ Warnings, cautions
INFO_BLUE = 0x3498DB        # ℹ️ Information, loading
```

#### Time-Based Colors

```python
MORNING_GOLD = 0xFFD700     # 🌅 6:00 - 12:00
AFTERNOON_ORANGE = 0xFF6B35 # ☀️ 12:00 - 17:00
EVENING_DARK = 0xFF8C00     # 🌆 17:00 - 20:00
NIGHT_BLUE = 0x4169E1       # 🌙 20:00 - 6:00
```

#### State Colors

```python
FINALIZED_RED = 0xFF1744    # 🏆 Completed orders
INACTIVE_GRAY = 0x95A5A6    # 🔒 Disabled/locked state
```

---

## 📝 Typography

### Text Formatting Rules

#### Headers

```markdown
Title: **ALL CAPS** with emojis
Example: 🍽️ **THỰC ĐƠN HÔM NAY** 🍽️
```

#### Inline Values

```markdown
Use backticks for values: `12` món
Use backticks for states: `ACTIVE`
Use backticks for codes: `#001`
```

#### Code Blocks

````markdown
# Info sections

```ansi
\u001b[1;36m━━━ SECTION NAME ━━━\u001b[0m
```
````

# Success messages

```diff
+ Positive message here +
```

# Error messages

```diff
- Negative message here -
```

````

---

## 🎯 Emoji Usage

### Food Category Emojis
```python
FOOD_EMOJIS = {
    "rice": "🍚",        # Cơm (rice dishes)
    "noodle": "🍜",      # Bún/Phở/Miến
    "meat": "🥩",        # Thịt (meat)
    "fish": "🐟",        # Cá (fish)
    "soup": "🍲",        # Canh (soup)
    "vegetable": "🥬",   # Rau (vegetables)
    "other": "🍽️"       # Other dishes
}
````

### System Emojis

```python
STATUS_EMOJIS = {
    "loading": "🔄",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "locked": "🔒",
    "unlocked": "🔓",
    "active": "🟢",
    "processing": "⚡"
}

TIME_EMOJIS = {
    "morning": "🌅",
    "afternoon": "☀️",
    "evening": "🌆",
    "night": "🌙"
}

UI_EMOJIS = {
    "cart": "🛒",
    "menu": "🍽️",
    "user": "👤",
    "stats": "📊",
    "trophy": "🏆",
    "package": "📦",
    "note": "📝"
}
```

---

## 🎨 Layout Patterns

### Box Borders

```
╔═══════════════════════════╗
║   CENTERED TITLE HERE     ║
╚═══════════════════════════╝
```

### Section Separators

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Tree Structure

```
┣━ Item 1
┃  └─ Detail
┣━ Item 2
┃  └─ Detail
┗━ Last Item
   └─ Detail
```

### Progress Bars

```python
# Full bar (15 characters max)
"█████████████░░"  # 87% filled

# Quantity indicators
"●●●●●"    # 5 items
"🟢🟢🟢+"  # More than 3 items
```

---

## 📱 Component Patterns

### Embed Structure

```python
embed = discord.Embed(
    title="✨ **TITLE IN CAPS** ✨",
    description="""
╔═══════════════════════════╗
║     SECTION HEADER        ║
╚═══════════════════════════╝

Main description text here...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
    color=COLOR_CODE
)
```

### Field Naming

```python
# Use emojis + bold + descriptive names
embed.add_field(
    name="📊 **ANALYTICS DASHBOARD**",
    value="...",
    inline=False
)
```

### Footer Pattern

```python
embed.set_footer(
    text="💡 Helpful tip here • Gordon Meow Meow AI Service 🤖",
    icon_url="URL_HERE"
)
```

---

## 🎮 Button Styles

### Button Configuration

```python
# Success/Primary Action
discord.ui.Button(
    label="Action Name",
    style=discord.ButtonStyle.success,
    emoji="✅",
    row=1
)

# Danger/Delete Action
discord.ui.Button(
    label="Delete",
    style=discord.ButtonStyle.danger,
    emoji="🗑️",
    row=1
)

# Secondary/Info Action
discord.ui.Button(
    label="View",
    style=discord.ButtonStyle.secondary,
    emoji="👁️",
    row=1
)

# Primary/Edit Action
discord.ui.Button(
    label="Edit",
    style=discord.ButtonStyle.primary,
    emoji="✏️",
    row=1
)
```

---

## 📋 Dropdown Menus

### Select Menu Pattern

```python
discord.ui.Select(
    placeholder="🎯 Action description with emoji...",
    min_values=1,
    max_values=1,
    options=[
        discord.SelectOption(
            label="Short name (20 chars)",
            value="internal_value",
            description="Helpful description",
            emoji="🥘"
        )
    ]
)
```

---

## 💬 Message Templates

### Success Messages

````python
f"""
```ansi
\u001b[1;32m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
   ✅ **SUCCESS MESSAGE**
\u001b[1;32m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
````

🎉 **Main success text**
📊 **Details:** `value`

```diff
+ Everything is good!
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

````

### Error Messages
```python
f"""
```ansi
\u001b[1;31m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
   ⚠️ **ERROR TYPE**
\u001b[1;31m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
````

❌ **Error description**

💡 **Solution:** How to fix

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

````

### Info Messages
```python
f"""
```ansi
\u001b[1;36m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
   ℹ️ **INFORMATION**
\u001b[1;36m━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m
````

ℹ️ **Info text here**
📋 **Details:** More info

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

````

---

## 📊 Data Visualization

### Statistics Display
```python
f"""
```ansi
\u001b[1;33m━━━ STATISTICS ━━━\u001b[0m
````

📊 **Metric:** `{value}`
⏰ **Time:** `{timestamp}`
👥 **Users:** `{count}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

````

### Progress Visualization
```python
# Calculate bar
max_value = max(values)
bar_length = int((current / max_value) * 15)
progress_bar = "█" * bar_length + "░" * (15 - bar_length)
percentage = int((current / total * 100))

# Display
f"┣━ **Item Name**\n"
f"┃  └─ `{current}` • `{percentage}%` • `{progress_bar}`\n"
````

---

## 🔤 Text Formatting

### Capitalization Rules

- **Titles**: ALL CAPS
- **Section Headers**: Title Case
- **Labels**: Sentence case
- **Values**: lowercase or as-is

### Spacing Rules

```python
# Between sections
"\n\n"

# Between items in list
"\n"

# Around separators
"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
```

---

## 🎯 Accessibility Guidelines

### Color Contrast

- Always use high-contrast color combinations
- Don't rely solely on color to convey information
- Include emoji/text indicators

### Text Clarity

- Use clear, descriptive labels
- Avoid jargon when possible
- Provide helpful error messages
- Include examples in placeholders

### Visual Hierarchy

1. **Most Important**: Title with emojis and formatting
2. **Secondary**: Section headers with emojis
3. **Tertiary**: Content with inline formatting
4. **Least Important**: Footer text

---

## 🚀 Performance Tips

### Emoji Usage

- Cache emoji mappings
- Use consistent emoji sets
- Limit unique emojis per message

### Text Length

- Truncate long names: `name[:20] + "..."`
- Use pagination for long lists
- Collapse detailed information

### Update Frequency

- Batch updates when possible
- Use defer() for slow operations
- Show loading states

---

## 📝 Code Style

### Naming Conventions

```python
# Embed creation functions
def create_menu_embed():
def create_order_summary_embed():
def create_finalized_order_embed():

# Color constants
SUCCESS_COLOR = 0x00D4AA
ERROR_COLOR = 0xE74C3C

# Component IDs
custom_id="action_name"
```

### Comment Style

```python
# Enhanced loading message with animation feel
# Create impressive success notification
# Sort by quantity for better visualization
```

---

## ✅ Quality Checklist

Before deploying new UI components:

- [ ] Colors match style guide
- [ ] Emojis are appropriate and consistent
- [ ] Text is properly formatted (bold, code, etc.)
- [ ] Borders and separators are aligned
- [ ] Mobile-friendly layout
- [ ] Error messages are helpful
- [ ] Success feedback is clear
- [ ] Loading states are indicated
- [ ] Timestamps are formatted consistently
- [ ] Values use backticks
- [ ] Headers use proper casing

---

**Last Updated:** November 7, 2025  
**Version:** 2.0  
**Status:** ✅ Active
