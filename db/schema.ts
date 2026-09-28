import { sqliteTable, text, integer, index, primaryKey } from 'drizzle-orm/sqlite-core';

export const appointments=sqliteTable('appointment_requests',{
 id:text('id').primaryKey(),
 requestKey:text('request_key').notNull().unique(),
 name:text('name').notNull(),
 email:text('email').notNull(),
 phone:text('phone').notNull(),
 address:text('address').notNull(),
 city:text('city').notNull(),
 service:text('service').notNull(),
 preferredDate:text('preferred_date').notNull(),
 period:text('period').notNull(),
 notes:text('notes').notNull().default(''),
 status:text('status').notNull().default('nieuw'),
 createdAt:integer('created_at').notNull(),
 updatedAt:integer('updated_at').notNull(),
 confirmedDate:text('confirmed_date'),
 confirmedTime:text('confirmed_time'),
 confirmationPayload:text('confirmation_payload'),
 confirmationStartedAt:integer('confirmation_started_at'),
 confirmationEmailId:text('confirmation_email_id'),
},table=>[index('idx_appointment_requests_created').on(table.createdAt)]);

export const requestLimits=sqliteTable('appointment_request_limits',{
 bucket:text('bucket').primaryKey(),
 count:integer('count').notNull().default(0),
 expiresAt:integer('expires_at').notNull(),
});

export const siteEvents=sqliteTable('site_events',{
 day:text('day').notNull(),
 path:text('path').notNull(),
 event:text('event').notNull(),
 count:integer('count').notNull().default(0),
},table=>[
 primaryKey({columns:[table.day,table.path,table.event]}),
 index('idx_site_events_day').on(table.day),
]);
