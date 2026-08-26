import ComparePage from "@/components/pages/compare-page";
import { fetchProgramRows } from "@/lib/programs-query";
import { enrichWithScores } from "@/lib/matching";

export const metadata = { title: "Compare" };
export const dynamic = "force-dynamic";

export default async function Page() {
  const { rows } = await fetchProgramRows();
  return <ComparePage rows={enrichWithScores(rows)} />;
}
