import CountryPage from "@/components/pages/country-page";
import { fetchCountryPage } from "@/lib/programs-query";

export const metadata = { title: "Country pack" };
export const dynamic = "force-dynamic";

export default async function Page({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  const { country, programs } = await fetchCountryPage(code);
  return <CountryPage country={country} programs={programs} />;
}
