from typact.core.types import SimpleResponse


class FileResponseConverter:
    def convert(self, response: SimpleResponse):
        if response.status_code >= 400:
            raise RuntimeError(response.content[:500])
        return response.content
