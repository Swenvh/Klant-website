CREATE TABLE `site_events` (
	`day` text NOT NULL,
	`path` text NOT NULL,
	`event` text NOT NULL,
	`count` integer DEFAULT 0 NOT NULL,
	PRIMARY KEY(`day`, `path`, `event`)
);
--> statement-breakpoint
CREATE INDEX `idx_site_events_day` ON `site_events` (`day`);