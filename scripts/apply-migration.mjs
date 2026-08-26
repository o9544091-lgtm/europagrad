import { readFileSync } from "node:fs";
import { Client } from "pg";

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  console.error(
    "Set DATABASE_URL first (Session pooler connection string from Supabase Dashboard -> Connect).",
  );
  process.exit(1);
}

const sql = readFileSync("supabase/migrations/0001_init.sql", "utf8");

const client = new Client({
  connectionString: DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

await client.connect();

try {
  await client.query(sql);
  console.log("migration applied");
} catch (err) {
  console.error("MIGRATION ERROR: " + err.message);
  await client.end();
  process.exit(1);
}

const verify = await client.query(`
  select
    (select count(*) from information_schema.tables where table_schema = 'public') as tables,
    (select count(*) from pg_type where typname in ('funding_class','opportunity_type','source_tier','match_class','scholarship_match','deadline_status','job_status','tracker_status')) as enums,
    (select count(*) from countries) as countries,
    (select count(*) from countries where is_launch_seed) as seeds,
    (select count(*) from pg_policies where schemaname = 'public') as policies
`);

console.log("verify:", verify.rows[0]);
await client.end();
