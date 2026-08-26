import { createClient } from "@/lib/supabase/server";
import { NextResponse, type NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }
  const body = await request.json().catch(() => null);
  const entityType = body?.entityType;
  const entityId = body?.entityId;
  if (entityType !== "PROGRAM" && entityType !== "SCHOLARSHIP") {
    return NextResponse.json({ error: "invalid entityType" }, { status: 400 });
  }
  if (typeof entityId !== "string" || !entityId) {
    return NextResponse.json({ error: "invalid entityId" }, { status: 400 });
  }
  const { error } = await supabase
    .from("saved_items")
    .upsert(
      { user_id: user.id, entity_type: entityType, entity_id: entityId },
      { onConflict: "user_id,entity_type,entity_id" },
    );
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
  return NextResponse.json({ ok: true });
}

export async function DELETE(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "sign in required" }, { status: 401 });
  }
  const { searchParams } = new URL(request.url);
  const entityType = searchParams.get("entityType");
  const entityId = searchParams.get("entityId");
  if ((entityType !== "PROGRAM" && entityType !== "SCHOLARSHIP") || !entityId) {
    return NextResponse.json({ error: "invalid params" }, { status: 400 });
  }
  const { error } = await supabase
    .from("saved_items")
    .delete()
    .eq("user_id", user.id)
    .eq("entity_type", entityType)
    .eq("entity_id", entityId);
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
  return NextResponse.json({ ok: true });
}
