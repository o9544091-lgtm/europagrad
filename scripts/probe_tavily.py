import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "agent" / "src"))

from europagrad_agent.search.provider import TavilyProvider  # noqa: E402


async def main() -> None:
    from europagrad_agent.config import get_settings

    s = get_settings()
    provider = TavilyProvider(api_key=s.tavily_api_key)
    results = await provider.search("government scholarship Italy international students masters", page=1, max_results=5)
    print(f"results: {len(results)}")
    for r in results[:5]:
        print(f"  {r.url} — {r.title[:60]}")


asyncio.run(main())
