import asyncio
from typing import Any

from falcon import File, HttpClient, MockRuntime


runtime = MockRuntime()
runtime.add_response(
    "POST",
    "http://test.local/upload",
    json_data={
        "ok": True,
    },
)

client = HttpClient(
    base_url="http://test.local",
    client_runtime=runtime,
)


@client.post("/upload")
async def upload_file(
    avatar: bytes = File(
        alias="file",
        filename="avatar.txt",
        content_type="text/plain",
    ),
) -> dict[str, Any]:
    pass


async def main():
    result = await upload_file(b"hello falcon")
    print("result:", result)

    request = runtime.requests[0]
    print("files:", request.files)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
