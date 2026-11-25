import { sqliteTable, text, integer, index, primaryKey } from 'drizzle-orm/sqlite-core';

// Offerteaanvragen via het formulier op /contact/.
export const quoteRequests=sqliteTable('quote_requests',{
 id:text('id').primaryKey(),
 requestKey:text('request_key').notNull().unique(),
 name:text('name').notNull(),
 email:text('email').notNull(),
 phone:text('phone').notNull().default(''),
 city:text('city').notNull(),
 customerType:text('customer_type').notNull().default('Particulier'),
 service:text('service').notNull(),
 mailOwnerId:text('mail_owner_id'),
 mailCustomerId:text('mail_customer_id'),
 status:text('status').notNull().default('nieuw'),
 createdAt:integer('created_at').notNull(),
 updatedAt:integer('updated_at').notNull(),
},table=>[index('idx_quote_requests_created').on(table.createdAt)]);

// Aanvragen per IP per uur (gehasht), tegen misbruik van het formulier.
export const requestLimits=sqliteTable('request_limits',{
 bucket:text('bucket').primaryKey(),
 count:integer('count').notNull().default(0),
 expiresAt:integer('expires_at').notNull(),
});

// Anonieme totaaltellingen per dag, pagina en actie.
export const siteEvents=sqliteTable('site_events',{
 day:text('day').notNull(),
 path:text('path').notNull(),
 event:text('event').notNull(),
 count:integer('count').notNull().default(0),
},table=>[
 primaryKey({columns:[table.day,table.path,table.event]}),
 index('idx_site_events_day').on(table.day),
]);
