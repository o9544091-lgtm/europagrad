"use client";

import { useCallback, useEffect, useState } from "react";

export interface PlanProgram {
  id: string;
  name: string;
  university: string;
  country: string;
  fundingClass: string;
  deadline: string | null;
  deadlineStatus: string;
}

export interface SavedItem {
  entityType: "PROGRAM" | "SCHOLARSHIP";
  entityId: string;
  note: string | null;
  createdAt: string;
  program: PlanProgram | null;
}

export interface TrackerItem {
  programId: string;
  status: string;
  updatedAt: string;
  program: PlanProgram | null;
}

export interface PlanData {
  saved: SavedItem[];
  tracker: TrackerItem[];
}

export const TRACKER_STAGES = [
  "INTERESTED",
  "RESEARCHING",
  "SHORTLISTED",
  "APPLIED",
  "SCHOLARSHIP_APPLIED",
  "RESULT",
] as const;

export const STAGE_LABELS: Record<(typeof TRACKER_STAGES)[number], string> = {
  INTERESTED: "Interested",
  RESEARCHING: "Researching",
  SHORTLISTED: "Shortlisted",
  APPLIED: "Applied",
  SCHOLARSHIP_APPLIED: "Scholarship applied",
  RESULT: "Result",
};

export function usePlan() {
  const [data, setData] = useState<PlanData | null>(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch("/api/plan", { cache: "no-store" });
      if (resp.status === 401) {
        setAuthRequired(true);
        setData(null);
        return;
      }
      setAuthRequired(false);
      if (resp.ok) setData(await resp.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const saveItem = useCallback(async (entityType: "PROGRAM" | "SCHOLARSHIP", entityId: string) => {
    const resp = await fetch("/api/plan/saved", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entityType, entityId }),
    });
    if (resp.status === 401) setAuthRequired(true);
    return resp.ok;
  }, []);

  const removeSaved = useCallback(async (entityType: "PROGRAM" | "SCHOLARSHIP", entityId: string) => {
    const resp = await fetch(`/api/plan/saved?entityType=${entityType}&entityId=${entityId}`, { method: "DELETE" });
    return resp.ok;
  }, []);

  const setTrackerStatus = useCallback(async (programId: string, status: string) => {
    const resp = await fetch("/api/plan/tracker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ programId, status }),
    });
    return resp.ok;
  }, []);

  const removeTracker = useCallback(async (programId: string) => {
    const resp = await fetch(`/api/plan/tracker?programId=${programId}`, { method: "DELETE" });
    return resp.ok;
  }, []);

  return { data, authRequired, loading, refresh, saveItem, removeSaved, setTrackerStatus, removeTracker };
}
