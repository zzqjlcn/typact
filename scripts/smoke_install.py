"""Verify the installed core wheel without optional HTTP dependencies."""

import asyncio
from importlib.resources import files
from importlib.util import find_spec

from typact import HttpClient, MockRuntime, RetryConfig, UrllibRuntime


async def main():
    assert find_spec("httpx") is None and find_spec("aiohttp") is None
    assert files("typact").joinpath("py.typed").is_file()
    assert isinstance(HttpClient("https://example.test").runtime, UrllibRuntime)
    runtime = MockRuntime()
    runtime.add_response("GET", "https://example.test/health", json_data={"ok": True})
    async with HttpClient("https://example.test", client_runtime=runtime) as client:
        @client.get("/health", retry_config=RetryConfig())
        async def health() -> dict:
            pass

        assert await health() == {"ok": True}
    print("Installed core wheel: imports, typing marker and request conversion passed")


if __name__ == "__main__":
    asyncio.run(main())
