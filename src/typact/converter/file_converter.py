from typact.core.types import Response


class FileResponseConverter:
    def convert(self, response: Response):
        if response.status_code >= 400:
            raise RuntimeError(response.content[:500])
        return response.content
