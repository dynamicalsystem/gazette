def url_join(base: str, fragments: list) -> str:
    """Join a base URL with path fragments, no trailing slash.

    e.g. url_join("http://signal:8080", ["v2/send"]) -> "http://signal:8080/v2/send"
    """
    parts = [base.rstrip("/")]
    for fragment in fragments:
        parts.append(str(fragment).strip("/"))

    return "/".join(parts)


def cli_hyperlink(url, label=None):
    if label is None:
        label = url
    parameters = ""

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

    return escape_mask.format(parameters, url, label)


def possessive(s):
    if s[-1] == "s":
        return f"{s}'"
    else:
        return f"{s}'s"
