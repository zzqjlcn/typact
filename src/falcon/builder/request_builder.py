import inspect
from typing import Any

from pydantic import TypeAdapter

from falcon.annotations.base import MISSING
from falcon.annotations.body import BodyParam
from falcon.annotations.cookie import CookieParam
from falcon.annotations.file import FileParam
from falcon.annotations.form import FormParam
from falcon.annotations.header import HeaderParam
from falcon.annotations.path import PathParam
from falcon.annotations.query import QueryParam
from falcon.builder.multipart_builder import MultipartBuilder
from falcon.builder.url_builder import PathValue, UrlBuilder
from falcon.client.metadata import RouteDefinition
from falcon.core.types import RequestConfig


def encode_value(value: Any) -> Any:
    return TypeAdapter(Any).dump_python(value, mode="json", by_alias=True)


class RequestBuilder:
    def __init__(
        self,
        base_url: str,
        default_headers: dict[str, str] | None = None,
    ):
        self.url_builder = UrlBuilder(base_url)
        self.default_headers = default_headers or {}
        self.multipart_builder = MultipartBuilder()

    def build(
        self,
        route: RouteDefinition,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> RequestConfig:
        bound = route.signature.bind_partial(*args, **kwargs)

        path_params: dict[str, Any] = {}
        query_params: dict[str, Any] = {}
        header_params: dict[str, Any] = {}
        cookie_params: dict[str, Any] = {}
        body_params: dict[str, Any] = {}
        form_params: dict[str, Any] = {}
        file_params: dict[str, tuple[FileParam, Any]] = {}

        for name, param in route.signature.parameters.items():
            marker = param.default

            if name in bound.arguments:
                value = bound.arguments[name]
            elif self._is_falcon_param(marker) and marker.default is not MISSING:
                value = marker.default
            elif param.default is not inspect._empty and not self._is_falcon_param(marker):
                value = param.default
            elif self._is_falcon_param(marker) and not marker.required:
                value = None
            else:
                raise TypeError(f"Missing required argument: {name}")

            if isinstance(marker, PathParam):
                path_value = PathValue(value=value, allow_slashes=marker.allow_slashes)
                path_params[marker.alias or name] = path_value
                path_params[name] = path_value

            elif isinstance(marker, QueryParam):
                key = marker.alias or name
                if value is not None:
                    query_params[key] = value

            elif isinstance(marker, HeaderParam):
                if marker.alias:
                    key = marker.alias
                elif marker.convert_underscores:
                    key = name.replace("_", "-")
                else:
                    key = name

                if value is not None:
                    header_params[key] = value

            elif isinstance(marker, CookieParam):
                key = marker.alias or name
                if value is not None:
                    cookie_params[key] = value

            elif isinstance(marker, BodyParam):
                key = marker.alias or name
                body_params[key] = value

            elif isinstance(marker, FileParam):
                file_params[name] = (marker, value)

            elif isinstance(marker, FormParam):
                key = marker.alias or name
                if value is not None:
                    form_params[key] = value

            elif value is not None:
                query_params[name] = value

        json_body = None

        if len(body_params) == 1:
            only_key = next(iter(body_params.keys()))
            only_value = body_params[only_key]

            original_param = self._find_body_param(route.signature)

            if original_param and original_param.embed:
                json_body = encode_value({only_key: only_value})
            else:
                json_body = encode_value(only_value)

        elif len(body_params) > 1:
            json_body = encode_value(body_params)

        return RequestConfig(
            method=route.method,
            url=self.url_builder.build(route.path, path_params),
            params=encode_value(query_params),
            headers={
                **self.default_headers,
                **encode_value(header_params),
            },
            cookies=encode_value(cookie_params),
            json=json_body,
            data=encode_value(form_params) if form_params else None,
            files=self.multipart_builder.build(file_params),
        )

    @staticmethod
    def _is_falcon_param(value: Any) -> bool:
        return isinstance(
            value,
            (
                PathParam,
                QueryParam,
                HeaderParam,
                CookieParam,
                BodyParam,
                FileParam,
                FormParam,
            ),
        )

    @staticmethod
    def _find_body_param(signature: inspect.Signature) -> BodyParam | None:
        for param in signature.parameters.values():
            if isinstance(param.default, BodyParam):
                return param.default
        return None
