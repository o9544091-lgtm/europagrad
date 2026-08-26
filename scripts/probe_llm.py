import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "agent" / "src"))

from europagrad_agent.extraction.service import ExtractionService  # noqa: E402

PAGE = """MSc Computer Science. The programme is taught entirely in English and takes 24 months to
complete. Tuition is EUR 1500 per year for non-EU students. IELTS 6.5 overall required.
Application deadline: 2027-03-15. Students may work part-time up to 20 hours per week."""


async def main() -> None:
    service = ExtractionService()
    for attempt in (1, 2):
        bundle, rejected = await service.extract("https://uni.edu/msc", PAGE)
        p = bundle.program
        print(f"attempt {attempt}: name={p.program_name.value if p.program_name else None} "
              f"ielts={p.ielts_overall.value if p.ielts_overall else None} "
              f"months={p.duration_months.value if p.duration_months else None} "
              f"tuition={p.tuition_eur_per_year.value if p.tuition_eur_per_year else None} "
              f"rejected={rejected}")


asyncio.run(main())
