import unicodedata

from pydantic import BaseModel, ConfigDict


class PublicModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_by_alias=True,
        validate_by_name=False,
        serialize_by_alias=True,
        hide_input_in_errors=True,
    )


def safe_text(value: str, *, multiline: bool = True) -> str:
    allowed = {"\n", "\t"} if multiline else set()
    if any(
        (unicodedata.category(char) in {"Cc", "Cs"} and char not in allowed)
        or char in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
        for char in value
    ):
        raise ValueError("Remove unsupported control characters.")
    return value
