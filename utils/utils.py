def format_title_case(text):
    """Format text in title case with special handling for conjunctions and parentheses."""
    conjunctions = {
        "and",
        "or",
        "but",
        "nor",
        "yet",
        "so",
        "for",
        "in",
        "to",
        "the",
        "a",
        "an",
    }

    if "(" in text and ")" in text:
        before_paren = text[: text.find("(")]
        in_paren = text[text.find("(") : text.find(")") + 1]
        after_paren = text[text.find(")") + 1 :]

        words_before = [
            word.capitalize() if word.lower() not in conjunctions else word.lower()
            for word in before_paren.split()
        ]
        words_in_paren = [
            word.capitalize() if word.lower() not in conjunctions else word.lower()
            for word in in_paren[1:-1].split()
        ]
        words_after = [
            word.capitalize() if word.lower() not in conjunctions else word.lower()
            for word in after_paren.split()
        ]

        if words_before:
            words_before[0] = words_before[0].capitalize()
        if words_in_paren:
            words_in_paren[0] = words_in_paren[0].capitalize()
        if words_after:
            words_after[0] = words_after[0].capitalize()

        return f"{' '.join(words_before)}({' '.join(words_in_paren)}){' '.join(words_after)}"
    else:
        words = text.split()
        result = []
        for i, word in enumerate(words):
            if i == 0:
                result.append(word.capitalize())
            else:
                result.append(
                    word.capitalize()
                    if word.lower() not in conjunctions
                    else word.lower()
                )
        return " ".join(result)


def format_salary(min_amount, max_amount, currency, interval):
    """Format salary with proper currency symbol."""
    if min_amount and max_amount:
        currency_symbol = "£" if currency == "GBP" else currency
        return f"{currency_symbol}{min_amount:,.0f} - {currency_symbol}{max_amount:,.0f} {interval}"
    return "Not specified"


import bleach
import markdown

def process_markdown(text):
    """Converts markdown text to sanitized HTML.

    This function takes a markdown string, converts it to HTML using the
    `markdown` library, and then sanitizes the HTML using `bleach` to
    prevent XSS attacks.

    Markdown Extensions Used:
        - nl2br: Converts newlines to <br> tags.
        - fenced_code: Allows for code blocks using backticks.

    Args:
        text (str): The markdown text to convert.

    Returns:
        str: The sanitized HTML output.
    """
    # Convert markdown to HTML with safe extensions
    html = markdown.markdown(
        text, extensions=["nl2br", "fenced_code"], output_format="html5"
    )

    # Clean the HTML output to prevent XSS
    allowed_tags = [
        "p",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "a",
        "code",
        "pre",
        "br",
        "hr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]
    allowed_attrs = {"a": ["href", "title", "target"]}

    clean_html = bleach.clean(
        html, tags=allowed_tags, attributes=allowed_attrs, strip=True
    )
    return clean_html
