"use client";

import { useEffect, useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { LoaderCircle, Mail, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const OPEN_AUTH_EVENT = "europagrad:open-auth";

export function openAuthDialog() {
  window.dispatchEvent(new CustomEvent(OPEN_AUTH_EVENT));
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AuthDialog() {
  const [open, setOpen] = useState(false);
  const [client, setClient] = useState<SupabaseClient | null>(null);
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener(OPEN_AUTH_EVENT, onOpen);
    return () => window.removeEventListener(OPEN_AUTH_EVENT, onOpen);
  }, []);

  useEffect(() => {
    if (!open || client) return;
    try {
      setClient(createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      ));
    } catch {
      toast.error("Authentication is not configured yet.");
      setOpen(false);
    }
  }, [open, client]);

  async function sendMagicLink() {
    if (!client) return;
    const value = email.trim();
    if (!EMAIL_RE.test(value)) {
      setEmailError("Enter a valid email address.");
      return;
    }
    setEmailError(null);
    setSending(true);
    const { error } = await client.auth.signInWithOtp({
      email: value,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    });
    setSending(false);
    if (error) {
      toast.error(error.message);
      return;
    }
    setSent(true);
  }

  async function signInWithGoogle() {
    if (!client) return;
    const { error } = await client.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      toast.error(
        error.message.includes("provider")
          ? "Google sign-in is not enabled yet. Use the email link for now."
          : error.message,
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" /> Sign in to EuropaGrad
          </DialogTitle>
          <DialogDescription>
            Browsing is open to everyone. A free account saves your profile,
            shortlist, and application tracker across devices.
          </DialogDescription>
        </DialogHeader>

        {sent ? (
          <div className="rounded-lg border border-primary/30 bg-primary/10 p-4 text-sm leading-6">
            <p className="font-bold">Check your inbox.</p>
            <p className="mt-1 text-muted-foreground">
              We sent a one-time sign-in link to{" "}
              <span className="font-semibold text-foreground">{email}</span>. It
              expires in one hour.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="auth-email">Email address</Label>
              <Input
                id="auth-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void sendMagicLink();
                }}
                aria-invalid={emailError ? true : undefined}
              />
              {emailError && (
                <p className="text-xs font-semibold text-destructive">
                  {emailError}
                </p>
              )}
            </div>
            <Button
              className="w-full gap-2"
              onClick={() => void sendMagicLink()}
              disabled={sending}
            >
              {sending ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <Mail className="h-4 w-4" />
              )}
              {sending ? "Sending link…" : "Email me a sign-in link"}
            </Button>
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-border" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                or
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => void signInWithGoogle()}
            >
              Continue with Google
            </Button>
            <p className="text-center text-[11px] leading-5 text-muted-foreground">
              No password, no spam. One link per sign-in.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
