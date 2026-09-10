import unittest
from collections.abc import AsyncIterator
from dataclasses import replace

from typact import (
    HttpClient, MockRuntime, Response, RetryConfig, default_should_retry_response,
)


class ResponseRetryTest(unittest.IsolatedAsyncioTestCase):
    async def test_network_retry_still_works_with_false_predicate(self):
        class FlakyRuntime(MockRuntime):
            attempts = 0

            async def request(self, config):
                self.attempts += 1
                if self.attempts == 1:
                    raise ConnectionError("temporary connection failure")
                return Response(200, {}, b"{}", {})

        runtime = FlakyRuntime()
        async with HttpClient(
            "https://example.test", client_runtime=runtime,
            retry_config=RetryConfig(
                max_retries=2, initial_delay=0, should_retry_response=lambda r: False,
            ),
        ) as client:
            @client.get("/test")
            async def request() -> dict:
                pass

            self.assertEqual(await request(), {})
        self.assertEqual(runtime.attempts, 2)

    async def test_explicit_post_permission(self):
        response = Response(200, {}, b"busy")
        _, requests, _ = await self.run_request(
            RetryConfig(
                max_retries=1, initial_delay=0, allowed_methods=frozenset({"POST"}),
                should_retry_response=lambda r: True,
            ),
            [response] * 2, method="POST",
        )
        self.assertEqual(len(requests), 2)

    async def run_request(self, policy, responses, *, method="GET", route_policy=...):
        runtime = MockRuntime()
        runtime.add_responses(method, "https://example.test/test", list(responses))
        events = []
        async with HttpClient(
            "https://example.test", client_runtime=runtime,
            retry_config=policy, event_handlers=[events.append],
        ) as client:
            options = {} if route_policy is ... else {"retry_config": route_policy}

            @client.request("/test", method=method, **options)
            async def request() -> Response:
                pass

            result = await request()
        return result, runtime.requests, events

    async def test_business_retry_receives_response_before_conversion(self):
        busy = Response(200, {"X-State": "busy"}, b"busy", {"code": "BUSY"})
        success = Response(200, {}, b"ok", {"code": "OK"})
        seen = []

        def predicate(response):
            seen.append(response)
            return response.json()["code"] == "BUSY"

        result, requests, events = await self.run_request(
            RetryConfig(max_retries=2, initial_delay=0, should_retry_response=predicate),
            [busy, success],
        )
        self.assertIs(result, success)
        self.assertEqual(seen, [busy, success])
        self.assertEqual(len(requests), 2)
        self.assertEqual([event.phase for event in events], ["request", "retry", "response"])
        self.assertIs(events[1].response, busy)
        self.assertEqual(events[-1].attempt, 2)

    async def test_callback_replaces_status_rule(self):
        response = Response(503, {}, b"busy")
        result, requests, _ = await self.run_request(
            RetryConfig(max_retries=2, should_retry_response=lambda r: False), [response],
        )
        self.assertIs(result, response)
        self.assertEqual(len(requests), 1)

    async def test_limits_skip_callback_and_exhaustion_returns_last_response(self):
        response = Response(200, {}, b"busy")
        for retries, method, expected_calls in [(0, "GET", 0), (2, "POST", 0), (2, "GET", 2)]:
            with self.subTest(retries=retries, method=method):
                seen = []

                def predicate(r):
                    seen.append(r)
                    return True

                result, requests, _ = await self.run_request(
                    RetryConfig(max_retries=retries, initial_delay=0, should_retry_response=predicate),
                    [response] * 3, method=method,
                )
                self.assertIs(result, response)
                self.assertEqual(len(seen), expected_calls)
                self.assertEqual(len(requests), expected_calls + 1)

    async def test_route_override_and_disable(self):
        response = Response(503, {}, b"busy")
        policy = RetryConfig(max_retries=1, initial_delay=0, should_retry_response=lambda r: False)
        for override, count in [(None, 1), (RetryConfig(max_retries=1, initial_delay=0), 2)]:
            with self.subTest(override=override):
                _, requests, _ = await self.run_request(policy, [response] * 2, route_policy=override)
                self.assertEqual(len(requests), count)

    async def test_callback_errors_are_not_network_retries(self):
        runtime = MockRuntime()
        runtime.add_response("GET", "https://example.test/test", json_data={})
        error = OSError("predicate failed")

        def predicate(response):
            raise error

        events = []
        async with HttpClient(
            "https://example.test", client_runtime=runtime, event_handlers=[events.append],
            retry_config=RetryConfig(max_retries=2, initial_delay=0, should_retry_response=predicate),
        ) as client:
            @client.get("/test")
            async def request() -> dict:
                pass

            with self.assertRaises(OSError) as caught:
                await request()
        self.assertIs(caught.exception, error)
        self.assertEqual(len(runtime.requests), 1)
        self.assertEqual([event.phase for event in events], ["request", "failure"])

    async def test_stream_rejects_callback_and_accepts_route_override(self):
        runtime = MockRuntime()
        runtime.add_stream_response("GET", "https://example.test/test", [b"ok"])
        async with HttpClient(
            "https://example.test", client_runtime=runtime,
            retry_config=RetryConfig(max_retries=1, should_retry_response=lambda r: True),
        ) as client:
            @client.get("/test")
            async def unsupported() -> AsyncIterator[bytes]:
                pass

            with self.assertRaisesRegex(ValueError, "not supported for streaming"):
                _ = [chunk async for chunk in unsupported()]
            self.assertEqual(runtime.requests, [])

            @client.get("/test", retry_config=RetryConfig(max_retries=1))
            async def supported() -> AsyncIterator[bytes]:
                pass

            self.assertEqual([chunk async for chunk in supported()], [b"ok"])

    def test_config_defaults_conflicts_and_replacement(self):
        self.assertEqual(RetryConfig().retry_status_codes, frozenset({429, 502, 503, 504}))
        for codes in [frozenset(), frozenset({503}), RetryConfig().retry_status_codes]:
            with self.subTest(codes=codes), self.assertRaisesRegex(ValueError, "mutually exclusive"):
                RetryConfig(retry_status_codes=codes, should_retry_response=lambda r: True)
        policy = RetryConfig(should_retry_response=default_should_retry_response)
        self.assertTrue(replace(policy, max_retries=2).matches_response(Response(503, {}, b"")))
        self.assertFalse(RetryConfig(retry_status_codes=frozenset()).matches_response(Response(503, {}, b"")))
        self.assertFalse(default_should_retry_response(Response(200, {}, b"")))

    def test_invalid_callbacks_and_results(self):
        async def asynchronous(response):
            return True

        for callback in [42, asynchronous]:
            with self.subTest(callback=callback), self.assertRaises(TypeError):
                RetryConfig(should_retry_response=callback)
        for result in [None, 1, "yes", asynchronous(None)]:
            with self.subTest(result=result), self.assertRaises(TypeError):
                RetryConfig(should_retry_response=lambda r: result).matches_response(Response(200, {}, b""))
