CREATE TABLE `appointment_requests` (
	`id` text PRIMARY KEY NOT NULL,
	`request_key` text NOT NULL,
	`name` text NOT NULL,
	`email` text NOT NULL,
	`phone` text NOT NULL,
	`address` text NOT NULL,
	`city` text NOT NULL,
	`service` text NOT NULL,
	`preferred_date` text NOT NULL,
	`period` text NOT NULL,
	`notes` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'nieuw' NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `appointment_requests_request_key_unique` ON `appointment_requests` (`request_key`);--> statement-breakpoint
CREATE INDEX `idx_appointment_requests_created` ON `appointment_requests` (`created_at`);--> statement-breakpoint
CREATE TABLE `appointment_request_limits` (
	`bucket` text PRIMARY KEY NOT NULL,
	`count` integer DEFAULT 0 NOT NULL,
	`expires_at` integer NOT NULL
);
