"use client";

import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "@/components/error-boundary";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <TooltipProvider>
        {children}
        <Toaster position="top-center" richColors closeButton />
      </TooltipProvider>
    </ErrorBoundary>
  );
}
