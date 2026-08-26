import ReportPage from "@/components/pages/report-page";
import { fetchProgramRows } from "@/lib/programs-query";
import { enrichWithScores } from "@/lib/matching";

export const metadata = { title: "Report" };
export const dynamic = "force-dynamic";

export default async function Page() {
  const { rows } = await fetchProgramRows();
  return <ReportPage rows={enrichWithScores(rows)} />;
}
