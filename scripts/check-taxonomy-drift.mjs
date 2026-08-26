import { readFileSync } from "node:fs";
import { Client } from "pg";

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error("Set DATABASE_URL (node --env-file=apps/agent/.env scripts/check-taxonomy-drift.mjs)");
  process.exit(1);
}

const ENUMS = [
  ["funding_class", "FundingClass"],
  ["opportunity_type", "OpportunityType"],
  ["source_tier", "SourceTier"],
  ["match_class", "MatchClass"],
  ["scholarship_match", "ScholarshipMatch"],
  ["deadline_status", "DeadlineStatus"],
  ["job_status", "JobStatus"],
  ["tracker_status", "TrackerStatus"],
];

const tsSource = readFileSync("apps/web/src/lib/db-types.ts", "utf8");
const pySource = readFileSync("apps/agent/src/europagrad_agent/taxonomy.py", "utf8");

function tsValues(typeName) {
  const match = tsSource.match(new RegExp(`export type ${typeName} =([\\s\\S]*?);`));
  if (!match) return null;
  return [...match[1].matchAll(/"([A-Z0-9_]+)"/g)].map((m) => m[1]);
}

function pyValues(className) {
  const match = pySource.match(
    new RegExp(`class ${className}\\(StrEnum\\):([\\s\\S]*?)\\n\\n`),
  );
  if (!match) return null;
  return [...match[1].matchAll(/= "([A-Z0-9_]+)"/g)].map((m) => m[1]);
}

const client = new Client({
  connectionString: DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});
await client.connect();

let failures = 0;

for (const [pgName, tsName] of ENUMS) {
  let dbValues;
  try {
    const res = await client.query(
      `select unnest(enum_range(null::${pgName}))::text as v order by v`,
    );
    dbValues = res.rows.map((r) => r.v);
  } catch (err) {
    console.log(`FAIL ${pgName}: missing in database (${err.message})`);
    failures += 1;
    continue;
  }

  const ts = tsValues(tsName);
  const py = pyValues(tsName);

  const dbSet = new Set(dbValues);
  const tsSet = new Set(ts ?? []);
  const pySet = new Set(py ?? []);

  const missingInTs = dbValues.filter((v) => !tsSet.has(v));
  const extraInTs = (ts ?? []).filter((v) => !dbSet.has(v));
  const missingInPy = dbValues.filter((v) => !pySet.has(v));
  const extraInPy = (py ?? []).filter((v) => !dbSet.has(v));

  if (missingInTs.length || extraInTs.length || missingInPy.length || extraInPy.length) {
    failures += 1;
    console.log(`FAIL ${pgName}:`);
    if (missingInTs.length) console.log(`  TS missing: ${missingInTs.join(", ")}`);
    if (extraInTs.length) console.log(`  TS extra:   ${extraInTs.join(", ")}`);
    if (missingInPy.length) console.log(`  PY missing: ${missingInPy.join(", ")}`);
    if (extraInPy.length) console.log(`  PY extra:   ${extraInPy.join(", ")}`);
  } else {
    console.log(`OK   ${pgName}: ${dbValues.length} values match in DB + TS + PY`);
  }
}

await client.end();

if (failures > 0) {
  console.log(`DRIFT DETECTED: ${failures} enum(s) out of sync`);
  process.exit(1);
}
console.log("taxonomy in sync: DB + TS + PY");
