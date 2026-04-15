from urllib.parse import quote
from fastapi.responses import RedirectResponse

def flash_redirect(url: str, message: str, category: str = "success"):
    return RedirectResponse(
        f"{url}?msg={quote(message)}&cat={category}", status_code=303
    )
