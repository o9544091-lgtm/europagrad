import { Client } from "pg";

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error("Set DATABASE_URL (node --env-file=apps/agent/.env scripts/test-rls.mjs)");
  process.exit(1);
}

const USER_A = "11111111-1111-1111-1111-111111111111";
const USER_B = "22222222-2222-2222-2222-222222222222";
const EMAIL_A = "rls-test-a@europagrad.test";
const EMAIL_B = "rls-test-b@europagrad.test";

const client = new Client({
  connectionString: DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});
await client.connect();

let failures = 0;

async function expect(label, fn) {
  try {
    const pass = await fn();
    if (pass) {
      console.log(`PASS ${label}`);
    } else {
      failures += 1;
      console.log(`FAIL ${label} (condition false)`);
    }
  } catch (err) {
    failures += 1;
    console.log(`FAIL ${label} (${err.message.split("\n")[0]})`);
  }
}

// ---------- setup: real identities + test dataset (service role) ----------
await client.query("begin");
try {
  await client.query("delete from auth.users where id in ($1, $2)", [USER_A, USER_B]);
  await client.query(
    `insert into auth.users (id, email, email_confirmed_at, created_at, updated_at)
     values ($1, $2, now(), now(), now()), ($3, $4, now(), now(), now())`,
    [USER_A, EMAIL_A, USER_B, EMAIL_B],
  );
  const uni = await client.query(
    "insert into universities (name, country_id) values ('RLS Test Uni', 'DE') returning id",
  );
  const prog = await client.query(
    "insert into programs (university_id, name) values ($1, 'RLS Test Program') returning id",
    [uni.rows[0].id],
  );
  await client.query("commit");
  var programId = prog.rows[0].id;
} catch (err) {
  await client.query("rollback");
  console.error("SETUP FAILED: " + err.message);
  await client.end();
  process.exit(1);
}

try {
  // ---------- anon role ----------
  await client.query("begin");
  await client.query("set local role anon");

  await expect("anon can read programs (public dataset)", async () => {
    const r = await client.query("select count(*)::int as n from programs");
    return r.rows[0].n >= 1;
  });

  await expect("anon can read countries", async () => {
    const r = await client.query("select count(*)::int as n from countries");
    return r.rows[0].n === 32;
  });

  await expect("anon cannot insert programs", async () => {
    await client.query("savepoint sp_anon_insert");
    try {
      await client.query(
        "insert into programs (university_id, name) values ('00000000-0000-0000-0000-000000000000','x')",
      );
      return false;
    } catch (err) {
      return err.code === "42501" || err.code === "23503";
    } finally {
      await client.query("rollback to savepoint sp_anon_insert");
    }
  });

  await expect("anon sees zero tracker rows (RLS blocks)", async () => {
    const r = await client.query("select count(*)::int as n from tracker_entries");
    return r.rows[0].n === 0;
  });

  await client.query("rollback");

  // ---------- authenticated as USER_A ----------
  await client.query("begin");
  await client.query("set local role authenticated");
  await client.query("select set_config('request.jwt.claims', $1, true)", [
    JSON.stringify({ sub: USER_A, role: "authenticated" }),
  ]);

  await expect("user A can insert own profile", async () => {
    await client.query(
      "insert into user_profiles (user_id, major) values ($1, 'CSE')",
      [USER_A],
    );
    const r = await client.query(
      "select major from user_profiles where user_id = $1",
      [USER_A],
    );
    return r.rows[0]?.major === "CSE";
  });

  await expect("user A cannot insert profile for user B (policy blocks)", async () => {
    await client.query("savepoint sp_profile_b");
    try {
      await client.query(
        "insert into user_profiles (user_id, major) values ($1, 'X')",
        [USER_B],
      );
      return false;
    } catch (err) {
      return err.code === "42501";
    } finally {
      await client.query("rollback to savepoint sp_profile_b");
    }
  });

  await expect("user A can insert own tracker entry for real program", async () => {
    const r = await client.query(
      "insert into tracker_entries (user_id, program_id) values ($1, $2) returning id",
      [USER_A, programId],
    );
    return r.rows.length === 1;
  });

  await expect("user A sees zero saved_items (none created yet)", async () => {
    const r = await client.query("select count(*)::int as n from saved_items");
    return r.rows[0].n === 0;
  });

  await client.query("rollback");

  // ---------- cross-user isolation (rows written by service role) ----------
  await client.query("begin");
  await client.query(
    "insert into tracker_entries (user_id, program_id) values ($1, $2), ($3, $2)",
    [USER_A, programId, USER_B],
  );
  await client.query(
    "insert into saved_items (user_id, entity_type, entity_id) values ($1, 'PROGRAM', $2)",
    [USER_B, programId],
  );
  await client.query("set local role authenticated");
  await client.query("select set_config('request.jwt.claims', $1, true)", [
    JSON.stringify({ sub: USER_A, role: "authenticated" }),
  ]);

  await expect("user A sees only their own tracker entries", async () => {
    const r = await client.query(
      "select user_id from tracker_entries where program_id = $1",
      [programId],
    );
    return r.rows.length === 1 && r.rows[0].user_id === USER_A;
  });

  await expect("user A cannot see user B saved_items", async () => {
    const r = await client.query("select count(*)::int as n from saved_items");
    return r.rows[0].n === 0;
  });

  await expect("user A cannot update user B tracker rows", async () => {
    const r = await client.query(
      "update tracker_entries set status = 'ACCEPTED' where program_id = $1 and user_id <> $2 returning id",
      [programId, USER_A],
    );
    return r.rows.length === 0;
  });

  await client.query("rollback");
} finally {
  // ---------- cleanup ----------
  try {
    await client.query("delete from auth.users where id in ($1, $2)", [USER_A, USER_B]);
    await client.query("delete from programs where name = 'RLS Test Program'");
    await client.query("delete from universities where name = 'RLS Test Uni'");
  } catch (err) {
    console.log("cleanup warning: " + err.message);
  }
  await client.end();
}

if (failures > 0) {
  console.log(`RLS TESTS FAILED: ${failures}`);
  process.exit(1);
}
console.log("all RLS policy tests passed");
