import asyncio

from pydantic import BaseModel, ConfigDict, Field

from falcon import (
    Body,
    Header,
    HttpClient,
    InterceptorChain,
    LoggingInterceptor,
    Path,
    Query,
    TraceIdInterceptor,
)


class Todo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    id: int | None = None
    title: str
    completed: bool


client = HttpClient(
    base_url="https://jsonplaceholder.typicode.com",
    headers={
        "User-Agent": "falcon/0.1.0",
    },
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            TraceIdInterceptor("demo-trace-id"),
            LoggingInterceptor(),
        ],
        response_interceptors=[
            LoggingInterceptor(),
        ],
    ),
)


@client.get("/todos")
def get_todos_sync() -> list[Todo]:
    pass


@client.get("/todos")
async def get_todos_async() -> list[Todo]:
    pass


@client.get("/todos/{todo_id}")
async def get_todo(
    todo_id: int = Path(),
    request_id: str = Header("req-001", alias="X-Request-Id"),
) -> Todo:
    pass


@client.get("/todos")
def query_todos(
    user_id: int | None = Query(None, alias="userId"),
) -> list[Todo]:
    pass


@client.post("/todos")
async def create_todo(
    todo: Todo = Body(),
) -> Todo:
    pass


async def main():
    todos1 = get_todos_sync()
    print("sync:", todos1[0])

    todos2 = await get_todos_async()
    print("async:", todos2[0])

    todo = await get_todo(1)
    print("one:", todo)

    queried = query_todos(user_id=1)
    print("query:", queried[0])

    created = await create_todo(
        Todo(
            user_id=1,
            title="hello falcon",
            completed=False,
        )
    )
    print("created:", created)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
