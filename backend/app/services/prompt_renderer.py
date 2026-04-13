from typing import Any


def render_template(template: str, row: dict[str, Any]) -> str:
    rendered = template
    for key, value in row.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered

