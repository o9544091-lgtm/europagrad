import ScholarshipDetailPage from "@/components/pages/scholarship-detail-page";

export const metadata = { title: "Scholarship dossier" };

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ScholarshipDetailPage id={id} />;
}
