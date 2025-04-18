CREATE TABLE IF NOT EXISTS `users` (
  `id` INTEGER PRIMARY KEY,
  `discord_id` varchar(20) NOT NULL UNIQUE,
  `username` varchar(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS `order` (
  `id` INTEGER PRIMARY KEY,
  `user_id` int(11) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `order_message_id` varchar(20) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `image_url` varchar(255),
  `status` TEXT CHECK(status IN ('pending', 'completed')) NOT NULL DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
);

CREATE TABLE IF NOT EXISTS `items` (
  `id` INTEGER PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  FOREIGN KEY (`order_id`) REFERENCES `order`(`id`)
);

CREATE TABLE IF NOT EXISTS `user_item` (
  `id` INTEGER PRIMARY KEY,
  `user_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT 1,
  FOREIGN KEY (`item_id`) REFERENCES `items`(`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
);