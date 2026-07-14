from typing import Any

from typact.annotations.file import FileParam


class MultipartBuilder:
    def build(self, file_params: dict[str, tuple[FileParam, Any]]) -> dict[str, Any]:
        files: dict[str, Any] = {}

        for name, (marker, value) in file_params.items():
            if value is None:
                continue

            field_name = marker.alias or name
            files[field_name] = self._build_file_value(field_name, marker, value)

        return files

    @staticmethod
    def _build_file_value(
        field_name: str,
        marker: FileParam,
        value: Any,
    ) -> Any:
        if isinstance(value, tuple):
            return value

        if marker.filename is None and marker.content_type is None:
            return value

        filename = marker.filename or getattr(value, "name", field_name)

        if marker.content_type is None:
            return (filename, value)

        return (filename, value, marker.content_type)
