import asyncio
from typing import Any

from typact import (
    ApiKeyInterceptor,
    BearerTokenInterceptor,
    HttpClient,
    InterceptorChain,
    MockRuntime,
)


runtime = MockRuntime()
runtime.add_response(
    "GET",
    "http://test.local/profile",
    json_data={
        "id": 1,
        "name": "typact",
    },
)

client = HttpClient(
    base_url="http://test.local",
    client_runtime=runtime,
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            BearerTokenInterceptor("demo-token"),
            ApiKeyInterceptor("demo-api-key"),
        ],
    ),
)


@client.get("/profile")
async def get_profile() -> dict[str, Any]:
    pass


async def main():
    profile = await get_profile()
    print("profile:", profile)

    request = runtime.requests[0]
    print("Authorization:", request.headers["Authorization"])
    print("X-API-Key:", request.headers["X-API-Key"])

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
