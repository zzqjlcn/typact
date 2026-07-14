import asyncio
from typing import Any

from typact import File, FileData, HttpClient, MockRuntime


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
    avatar: FileData = File(alias="file"),
) -> dict[str, Any]:
    pass


async def main():
    result = await upload_file(
        FileData(
            content=b"hello typact",
            filename="avatar.txt",
            content_type="text/plain",
        )
    )
    print("result:", result)

    request = runtime.requests[0]
    print("files:", request.files)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
