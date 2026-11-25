CREATE TABLE `quote_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`request_key` text NOT NULL,
	`name` text NOT NULL,
	`email` text NOT NULL,
	`phone` text DEFAULT '' NOT NULL,
	`city` text NOT NULL,
	`customer_type` text NOT NULL DEFAULT 'Particulier',
	`service` text NOT NULL,
	`mail_owner_id` text,
	`mail_customer_id` text,
	`status` text DEFAULT 'nieuw' NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `quote_requests_request_key_unique` ON `quote_requests` (`request_key`);--> statement-breakpoint
CREATE INDEX `idx_quote_requests_created` ON `quote_requests` (`created_at`);--> statement-breakpoint
CREATE TABLE `request_limits` (
	`bucket` text PRIMARY KEY NOT NULL,
	`count` integer DEFAULT 0 NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `site_events` (
	`day` text NOT NULL,
	`path` text NOT NULL,
	`event` text NOT NULL,
	`count` integer DEFAULT 0 NOT NULL,
	PRIMARY KEY(`day`, `path`, `event`)
);
--> statement-breakpoint
CREATE INDEX `idx_site_events_day` ON `site_events` (`day`);