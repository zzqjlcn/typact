import asyncio
import unittest
from collections.abc import AsyncIterator

from typact import HttpClient, Response, RetryConfig, TypactHttpError


class IntegrationApi:
    def __init__(self, client: HttpClient):
        client.request("/health", method="GET")(self.health)
        client.request("/stream", method="GET")(self.stream)
        client.request("/events", method="GET")(self.events)
        client.request("/error", method="GET")(self.error_stream)

    async def health(self) -> dict[str, bool]:
        raise NotImplementedError

    async def stream(self) -> AsyncIterator[bytes]:
        raise NotImplementedError

    async def events(self) -> AsyncIterator[dict[str, int]]:
        raise NotImplementedError

    async def error_stream(self) -> AsyncIterator[bytes]:
        raise NotImplementedError


class RuntimeIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_response_predicate_across_all_runtimes(self):
        from typact import AioHttpRuntime, HttpxRuntime, UrllibRuntime

        for runtime in (UrllibRuntime(), HttpxRuntime(), AioHttpRuntime()):
            with self.subTest(runtime=type(runtime).__name__):
                responses = []

                def predicate(response):
                    responses.append(response)
                    return True

                async with HttpClient(
                    self.base_url, client_runtime=runtime,
                    retry_config=RetryConfig(
                        max_retries=1, initial_delay=0, should_retry_response=predicate,
                    ),
                ) as client:
                    events = []
                    client.add_event_handler(events.append)
                    self.assertEqual(await IntegrationApi(client).health(), {"ok": True})
                self.assertEqual(len(responses), 1)
                self.assertIsInstance(responses[0], Response)
                self.assertEqual(responses[0].json(), {"ok": True})
                self.assertEqual(responses[0].status_code, 200)
                self.assertEqual([event.phase for event in events], ["request", "retry", "response"])

    async def asyncSetUp(self):
        self.server = await asyncio.start_server(self._handle_connection, "127.0.0.1", 0)
        port = self.server.sockets[0].getsockname()[1]
        self.base_url = f"http://127.0.0.1:{port}"

    async def asyncTearDown(self):
        self.server.close()
        self.server.close_clients()
        await self.server.wait_closed()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        try:
            await self._respond(reader, writer)
        except ConnectionError:
            # A client may intentionally close a stream before the response ends.
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    async def _respond(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        request_line = await reader.readline()
        if not request_line:
            return
        path = request_line.split()[1].decode()

        while True:
            line = await reader.readline()
            if not line:
                return
            if line == b"\r\n":
                break

        if path == "/health":
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                b"Content-Length: 12\r\nConnection: close\r\n\r\n{\"ok\": true}"
            )
        elif path == "/error":
            writer.write(
                b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 4\r\n"
                b"Connection: close\r\n\r\nnope"
            )
        elif path == "/stream":
            await self._write_chunked(writer, [b"first", b"-second"])
        elif path == "/events":
            await self._write_chunked(
                writer,
                [b"data: {\"value\": 1}\n\n", b"data: {\"value\": 2}\n\n"],
                content_type="text/event-stream",
            )

        await writer.drain()

    @staticmethod
    async def _write_chunked(
        writer: asyncio.StreamWriter,
        chunks: list[bytes],
        *,
        content_type: str = "application/octet-stream",
    ):
        writer.write(
            f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n"
            "Transfer-Encoding: chunked\r\nConnection: close\r\n\r\n".encode()
        )
        for chunk in chunks:
            writer.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
            await writer.drain()
            await asyncio.sleep(0)
        writer.write(b"0\r\n\r\n")

    async def test_httpx_and_aiohttp_runtime_behave_consistently(self):
        from typact import AioHttpRuntime, HttpxRuntime

        for runtime in (HttpxRuntime(), AioHttpRuntime()):
            async with HttpClient(self.base_url, client_runtime=runtime) as client:
                api = IntegrationApi(client)

                self.assertEqual(await api.health(), {"ok": True})
                # Runtime buffering may split or combine HTTP chunks.
                chunks = [chunk async for chunk in api.stream()]
                self.assertEqual(b"".join(chunks), b"first-second")
                self.assertEqual(
                    [event async for event in api.events()],
                    [{"value": 1}, {"value": 2}],
                )

                with self.assertRaises(TypactHttpError) as error:
                    async for _ in api.error_stream():
                        pass
                self.assertEqual(error.exception.status_code, 503)
                self.assertEqual(error.exception.content, b"nope")

    async def test_stream_can_be_closed_before_iteration_finishes(self):
        from typact import HttpxRuntime

        async with HttpClient(self.base_url, client_runtime=HttpxRuntime()) as client:
            api = IntegrationApi(client)
            stream = api.stream()

            first_chunk = await anext(stream)
            self.assertTrue(first_chunk)
            self.assertTrue(b"first-second".startswith(first_chunk))
            await stream.aclose()
            with self.assertRaises(StopAsyncIteration):
                await anext(stream)
