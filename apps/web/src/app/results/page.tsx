import ResultsPage from "@/components/pages/results-page";
import { fetchProgramRows } from "@/lib/programs-query";
import { enrichWithScores } from "@/lib/matching";

export const metadata = { title: "Results" };
export const dynamic = "force-dynamic";

export default async function Page() {
  const { rows, evidenceCounts } = await fetchProgramRows();
  return <ResultsPage rows={enrichWithScores(rows)} evidenceCounts={evidenceCounts} />;
}
