import ErasmusPage from "@/components/pages/erasmus-page";
import { fetchProgramRows } from "@/lib/programs-query";

export const metadata = { title: "Erasmus+" };
export const dynamic = "force-dynamic";

export default async function Page() {
  const { rows } = await fetchProgramRows();
  return <ErasmusPage rows={rows.filter((row) => row.isJointProgram)} />;
}
