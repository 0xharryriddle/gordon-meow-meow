import aiosqlite
import datetime

class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    # User management
    async def get_or_create_user(self, discord_id: int, username: str) -> int:
        """
        Get a user by discord_id or create if not exists.
        
        :param discord_id: Discord user ID
        :param username: Discord username
        :return: Database user ID
        """
        # Check if user exists
        rows = await self.connection.execute(
            "SELECT id FROM users WHERE discord_id = ?",
            (discord_id,)
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            if result is not None:
                return result[0]
            
            # Create new user
            await self.connection.execute(
                "INSERT INTO users(discord_id, username) VALUES (?, ?)",
                (discord_id, username)
            )
            await self.connection.commit()
            
            # Get the new user ID
            rows = await self.connection.execute(
                "SELECT id FROM users WHERE discord_id = ?",
                (discord_id,)
            )
            async with rows as cursor:
                result = await cursor.fetchone()
                return result[0]
    
    # Order management
    async def create_order(self, user_id: int, server_id: int, order_message_id: int) -> int:
        """
        Create a new order.
        
        :param user_id: Database user ID
        :param server_id: Discord server ID
        :param order_message_id: Discord message ID containing the order
        :return: Database order ID
        """
        await self.connection.execute(
            "INSERT INTO `order`(user_id, server_id, order_message_id) VALUES (?, ?, ?)",
            (user_id, server_id, order_message_id)
        )
        await self.connection.commit()
        
        # Get the new order ID
        rows = await self.connection.execute(
            "SELECT last_insert_rowid()"
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0]
    
    async def create_item(self, order_id: int, name: str) -> int:
        """
        Create a new item in an order.
        
        :param order_id: Database order ID
        :param name: Item name
        :return: Database item ID
        """
        await self.connection.execute(
            "INSERT INTO items(order_id, name) VALUES (?, ?)",
            (order_id, name)
        )
        await self.connection.commit()
        
        # Get the new item ID
        rows = await self.connection.execute(
            "SELECT last_insert_rowid()"
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0]
    
    async def add_user_item(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """
        Add an item to a user's order items.
        
        :param user_id: Database user ID
        :param item_id: Database item ID
        :param quantity: Quantity of items
        :return: Success boolean
        """
        # Check if user already has this item
        rows = await self.connection.execute(
            "SELECT id, quantity FROM user_item WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            
            if result is not None:
                # Update existing quantity
                await self.connection.execute(
                    "UPDATE user_item SET quantity = ? WHERE id = ?",
                    (result[1] + quantity, result[0])
                )
            else:
                # Create new user_item
                await self.connection.execute(
                    "INSERT INTO user_item(user_id, item_id, quantity) VALUES (?, ?, ?)",
                    (user_id, item_id, quantity)
                )
                
        await self.connection.commit()
        return True
    
    async def get_order_items(self, order_id: int) -> list:
        """
        Get all items in an order with their users and quantities.
        
        :param order_id: Database order ID
        :return: List of items with user details
        """
        rows = await self.connection.execute(
            """
            SELECT i.id, i.name, u.discord_id, u.username, ui.quantity 
            FROM items i
            JOIN user_item ui ON i.id = ui.item_id
            JOIN users u ON ui.user_id = u.id
            WHERE i.order_id = ?
            """,
            (order_id,)
        )
        async with rows as cursor:
            results = await cursor.fetchall()
            items_list = []
            for row in results:
                items_list.append({
                    'item_id': row[0],
                    'name': row[1],
                    'discord_id': row[2],
                    'username': row[3],
                    'quantity': row[4]
                })
            return items_list
    
    async def get_order_details(self, order_id: int) -> dict:
        """
        Get complete details of an order.
        
        :param order_id: Database order ID
        :return: Order details dictionary
        """
        # Get order information
        rows = await self.connection.execute(
            """
            SELECT o.id, o.server_id, o.order_message_id, o.total_amount, 
                  o.image_url, o.status, o.created_at, u.discord_id, u.username
            FROM `order` o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
            """,
            (order_id,)
        )
        async with rows as cursor:
            order_data = await cursor.fetchone()
            if not order_data:
                return None
            
            # Get all items in this order
            items = await self.get_order_items(order_id)
            
            return {
                'id': order_data[0],
                'server_id': order_data[1],
                'order_message_id': order_data[2],
                'total_amount': order_data[3],
                'image_url': order_data[4],
                'status': order_data[5],
                'created_at': order_data[6],
                'creator_discord_id': order_data[7],
                'creator_username': order_data[8],
                'items': items
            }
    
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """
        Update the status of an order.
        
        :param order_id: Database order ID
        :param status: New status ('pending' or 'completed')
        :return: Success boolean
        """
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.connection.execute(
            "UPDATE `order` SET status = ?, updated_at = ? WHERE id = ?",
            (status, current_time, order_id)
        )
        await self.connection.commit()
        return True
    
    async def update_order_total(self, order_id: int, total_amount: float) -> bool:
        """
        Update the total amount of an order.
        
        :param order_id: Database order ID
        :param total_amount: New total amount
        :return: Success boolean
        """
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await self.connection.execute(
            "UPDATE `order` SET total_amount = ?, updated_at = ? WHERE id = ?",
            (total_amount, current_time, order_id)
        )
        await self.connection.commit()
        return True
    
    async def get_orders(self, server_id: str, order_message_id: str) -> list:
        """
        Get all active (pending) orders for a server.
        
        :param server_id: Discord server ID
        :return: List of active orders
        """
        rows = await self.connection.execute(
            """
            SELECT o.id, o.order_message_id, o.total_amount, o.created_at, u.username
            FROM `order` o
            JOIN users u ON o.user_id = u.id
            WHERE o.server_id = ? AND o.order_message_id = ?
            ORDER BY o.created_at DESC
            """,
            (server_id,order_message_id)
        )
        async with rows as cursor:
            results = await cursor.fetchall()
            orders_list = []
            for row in results:
                orders_list.append({
                    'id': row[0],
                    'order_message_id': row[1],
                    'total_amount': row[2],
                    'created_at': row[3],
                    'creator_username': row[4]
                })
            return orders_list
    
    async def delete_order(self, order_id: int) -> bool:
        """
        Delete an order and all associated records.
        
        :param order_id: Database order ID
        :return: Success boolean
        """
        # Get all items in the order
        rows = await self.connection.execute(
            "SELECT id FROM items WHERE order_id = ?",
            (order_id,)
        )
        item_ids = []
        async with rows as cursor:
            results = await cursor.fetchall()
            for row in results:
                item_ids.append(row[0])
        
        # Delete user_item entries
        for item_id in item_ids:
            await self.connection.execute(
                "DELETE FROM user_item WHERE item_id = ?",
                (item_id,)
            )
        
        # Delete items
        await self.connection.execute(
            "DELETE FROM items WHERE order_id = ?",
            (order_id,)
        )
        
        # Delete order
        await self.connection.execute(
            "DELETE FROM `order` WHERE id = ?",
            (order_id,)
        )
        
        await self.connection.commit()
        return True

    async def get_active_order_by_message(self, message_id: str) -> int:
        """
        Get order ID from a message ID
        
        :param message_id: Discord message ID of the order
        :return: Database order ID or None if not found
        """
        rows = await self.connection.execute(
            "SELECT id FROM `order` WHERE order_message_id = ? AND status = 'pending'",
            (message_id,)
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None
