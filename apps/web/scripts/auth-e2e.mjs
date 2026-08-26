import { createClient } from "@supabase/supabase-js";

const url = process.env.SUPABASE_URL;
const serviceKey = process.env.SUPABASE_SERVICE_KEY;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!url || !serviceKey || !anonKey) {
  console.error("Need SUPABASE_URL, SUPABASE_SERVICE_KEY, NEXT_PUBLIC_SUPABASE_ANON_KEY in env.");
  process.exit(1);
}

const admin = createClient(url, serviceKey, { auth: { autoRefreshToken: false } });
const email = `auth-e2e-${Date.now()}@europagrad.test`;
const password = "E2e-Test-Passw0rd!";
let failures = 0;

function check(label, pass, detail = "") {
  if (pass) console.log(`PASS ${label}`);
  else {
    failures += 1;
    console.log(`FAIL ${label} ${detail}`);
  }
}

// 1. Admin creates a confirmed user
const { data: created, error: createErr } = await admin.auth.admin.createUser({
  email,
  password,
  email_confirm: true,
});
check("admin creates confirmed user", !!created?.user && !createErr, createErr?.message ?? "");
const userId = created?.user?.id;
if (!userId) process.exit(1);

try {
  // 2. Sign in with password via anon client (public flow)
  const client = createClient(url, anonKey);
  const { data: signed, error: signErr } = await client.auth.signInWithPassword({
    email,
    password,
  });
  check("sign-in with email + password returns session", !!signed.session && !signErr, signErr?.message ?? "");

  // 3. Authenticated write through RLS: own profile
  const { error: upsertErr } = await client
    .from("user_profiles")
    .upsert({ user_id: userId, major: "CSE", cgpa: 3.6 });
  check("signed-in user upserts own profile via API", !upsertErr, upsertErr?.message ?? "");

  const { data: profile, error: selErr } = await client
    .from("user_profiles")
    .select("major, cgpa")
    .eq("user_id", userId)
    .maybeSingle();
  check("signed-in user reads own profile back", profile?.major === "CSE" && !selErr, selErr?.message ?? "");

  // 4. Cannot see profiles of other users (isolation)
  const { data: others } = await client
    .from("user_profiles")
    .select("user_id")
    .neq("user_id", userId);
  check("user sees no other users' profiles", (others ?? []).length === 0);

  // 5. Anonymous client (signed out) sees zero profiles
  const anon = createClient(url, anonKey);
  const { data: anonView } = await anon.from("user_profiles").select("user_id");
  check("signed-out client sees zero profiles", (anonView ?? []).length === 0);

  // 6. Sign out
  await client.auth.signOut();
  const { data: after } = await client.auth.getSession();
  check("sign-out clears session", !after.session);
} finally {
  // 7. Cleanup
  const del = await admin.auth.admin.deleteUser(userId);
  check("cleanup: test user deleted", !del.error, del.error?.message ?? "");
}

if (failures > 0) {
  console.log(`AUTH E2E FAILED: ${failures}`);
  process.exit(1);
}
console.log("all auth e2e tests passed");
