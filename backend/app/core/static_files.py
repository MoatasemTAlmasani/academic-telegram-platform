"""Public static-file serving with explicit sensitive-artifact filtering."""

from __future__ import annotations

import re

from starlette.responses import PlainTextResponse, Response
from starlette.staticfiles import StaticFiles

_BACKUP_OR_TEMP_NAME = re.compile(
    r"(^|[._-])(backup|bak|before|previous|tmp|temp|development)([._-]|$)",
    re.IGNORECASE,
)


class PublicStaticFiles(StaticFiles):
    """Deny dotfiles and backup/development artifacts from public mounts."""

    async def get_response(self, path: str, scope) -> Response:
        segments = [segment for segment in path.replace("\\", "/").split("/") if segment]
        if any(
            segment.startswith(".")
            or _BACKUP_OR_TEMP_NAME.search(segment)
            for segment in segments
        ):
            return PlainTextResponse("Not found", status_code=404)
        return await super().get_response(path, scope)
