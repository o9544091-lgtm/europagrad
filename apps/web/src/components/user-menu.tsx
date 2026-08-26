"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createBrowserClient } from "@supabase/ssr";
import type { Session } from "@supabase/supabase-js";
import { LogOut, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AuthDialog, openAuthDialog } from "@/components/auth-dialog";

export function UserMenu() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    try {
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      );
      void supabase.auth.getSession().then(({ data }) => {
        if (mounted) {
          setSession(data.session);
          setReady(true);
        }
      });
      const { data } = supabase.auth.onAuthStateChange((_event, newSession) => {
        setSession(newSession);
      });
      return () => {
        mounted = false;
        data.subscription.unsubscribe();
      };
    } catch {
      setReady(true);
      return;
    }
  }, []);

  const email = session?.user.email ?? null;

  return (
    <>
      {ready && !session && (
        <Button
          variant="outline"
          size="sm"
          className="hidden gap-1.5 sm:inline-flex"
          onClick={openAuthDialog}
        >
          <UserRound className="h-3.5 w-3.5" /> Sign in
        </Button>
      )}
      {session && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="hidden max-w-40 gap-1.5 sm:inline-flex">
              <UserRound className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{email ?? "Account"}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="truncate">{email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/plan">My plan</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <form action="/auth/sign-out" method="post" className="w-full">
                <button
                  type="submit"
                  className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-secondary"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </form>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      <AuthDialog />
    </>
  );
}
