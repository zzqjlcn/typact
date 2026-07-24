import asyncio
from typing import Any

from typact import (
    CallableTokenProvider,
    HttpClient,
    InterceptorChain,
    MockRuntime,
    RefreshableBearerTokenInterceptor,
    Response,
)


async def login() -> str:
    print("refresh token")
    return "new-token"


runtime = MockRuntime()
runtime.add_responses(
    "GET",
    "http://test.local/profile",
    [
        Response(
            status_code=401,
            headers={},
            content=b'{"detail":"token expired"}',
            json_data={"detail": "token expired"},
        ),
        Response(
            status_code=200,
            headers={},
            content=b'{"id":1,"name":"typact"}',
            json_data={"id": 1, "name": "typact"},
        ),
    ],
)

token_provider = CallableTokenProvider(
    login,
    token="expired-token",
)

client = HttpClient(
    base_url="http://test.local",
    client_runtime=runtime,
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            RefreshableBearerTokenInterceptor(token_provider),
        ],
    ),
)


@client.get("/profile")
async def get_profile() -> dict[str, Any]:
    pass


async def main():
    profile = await get_profile()
    print("profile:", profile)

    first_request = runtime.requests[0]
    retry_request = runtime.requests[1]

    print("first Authorization:", first_request.headers["Authorization"])
    print("retry Authorization:", retry_request.headers["Authorization"])

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
