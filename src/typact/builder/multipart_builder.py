from typing import Any

from typact.annotations.file import FileData, FileParam


class MultipartBuilder:
    def build(self, file_params: dict[str, tuple[FileParam, Any]]) -> dict[str, Any]:
        files: dict[str, Any] = {}

        for name, (marker, value) in file_params.items():
            if value is None:
                continue

            field_name = marker.alias or name
            files[field_name] = self._build_file_value(field_name, value)

        return files

    @staticmethod
    def _build_file_value(
        field_name: str,
        value: Any,
    ) -> Any:
        if not isinstance(value, FileData):
            return value

        filename = value.filename or getattr(value.content, "name", field_name)

        if value.content_type is None:
            return (filename, value.content)

        return (filename, value.content, value.content_type)
