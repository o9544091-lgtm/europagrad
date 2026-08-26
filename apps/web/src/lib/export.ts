import * as XLSX from "xlsx";
import type { ProgramRow } from "@/lib/types";

export type ExportFormat = "csv" | "xlsx" | "json";

const COLUMNS: Array<{ key: keyof ProgramRow | "evidenceCount"; header: string }> = [
  { key: "rank", header: "Rank" },
  { key: "country", header: "Country" },
  { key: "university", header: "University" },
  { key: "program", header: "Programme" },
  { key: "degree", header: "Degree" },
  { key: "fieldTags", header: "Fields" },
  { key: "language", header: "Language" },
  { key: "durationMonths", header: "Duration (months)" },
  { key: "tuitionEurPerYear", header: "Tuition EUR/yr" },
  { key: "fundingClass", header: "Funding" },
  { key: "scholarshipName", header: "Scholarship" },
  { key: "ieltsOverall", header: "IELTS" },
  { key: "moiAccepted", header: "MOI" },
  { key: "intake", header: "Intake" },
  { key: "deadline", header: "Deadline" },
  { key: "deadlineStatus", header: "Deadline status" },
  { key: "daysRemaining", header: "Days remaining" },
  { key: "partTimeWork", header: "Part-time" },
  { key: "matchClass", header: "Match" },
  { key: "score", header: "Score" },
  { key: "evidenceCount", header: "Evidence entries" },
];

export function toExportRecords(rows: ProgramRow[], evidenceCounts: Record<string, number> = {}): Record<string, unknown>[] {
  return rows.map((row) => {
    const record: Record<string, unknown> = {};
    for (const { key, header } of COLUMNS) {
      if (key === "evidenceCount") {
        record[header] = evidenceCounts[row.id] ?? 0;
        continue;
      }
      const value = row[key];
      record[header] = Array.isArray(value) ? value.join(" | ") : value;
    }
    return record;
  });
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function exportPrograms(
  rows: ProgramRow[],
  format: ExportFormat,
  evidenceCounts: Record<string, number> = {},
) {
  if (rows.length === 0) return;
  const records = toExportRecords(rows, evidenceCounts);
  const stamp = new Date().toISOString().slice(0, 10);
  if (format === "json") {
    const blob = new Blob([JSON.stringify(records, null, 2)], { type: "application/json" });
    download(blob, `europagrad-programmes-${stamp}.json`);
    return;
  }
  const sheet = XLSX.utils.json_to_sheet(records);
  if (format === "csv") {
    const csv = XLSX.utils.sheet_to_csv(sheet);
    download(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }), `europagrad-programmes-${stamp}.csv`);
    return;
  }
  const book = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(book, sheet, "Programmes");
  const out = XLSX.write(book, { bookType: "xlsx", type: "array" });
  download(
    new Blob([out], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }),
    `europagrad-programmes-${stamp}.xlsx`,
  );
}
