import { notFound } from "next/navigation";
import ProgramDetailPage from "@/components/pages/program-detail-page";
import { fetchProgramById } from "@/lib/programs-query";

export const metadata = { title: "Programme dossier" };
export const dynamic = "force-dynamic";

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const result = await fetchProgramById(id);
  if (!result) notFound();
  return <ProgramDetailPage program={result.program} evidence={result.evidence} changes={result.changes} />;
}
