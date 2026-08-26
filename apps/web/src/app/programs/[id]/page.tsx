import ProgramDetailPage from "@/components/pages/program-detail-page";

export const metadata = { title: "Programme dossier" };

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ProgramDetailPage id={id} />;
}
