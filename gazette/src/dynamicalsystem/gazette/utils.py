from urllib.parse import urljoin


def url_join(base: str, fragments: list):
    for fragment in fragments:
        if fragment[-1] != "/":
            fragment += "/"
        base = urljoin(base, fragment, allow_fragments=True)

    return base


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
