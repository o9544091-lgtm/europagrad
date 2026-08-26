import CountryPage from "@/components/pages/country-page";

export const metadata = { title: "Country pack" };

export default async function Page({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  return <CountryPage code={code} />;
}
