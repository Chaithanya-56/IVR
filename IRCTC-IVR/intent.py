import re


def detect_intent(text):

    text = text.lower()

    if "book" in text and "ticket" in text:
        return "book_ticket"

    if "pnr" in text or "status" in text:
        return "pnr_status"

    if "cancel" in text:
        return "cancel_ticket"

    if "change destination" in text:
        return "change_destination"

    if "change date" in text:
        return "change_date"

    if "seat" in text or "availability" in text:
        return "seat_check"

    return "unknown"


def extract_booking_details(text):

    text = text.lower()

    match = re.search(r"from\s+([a-zA-Z]+)\s+to\s+([a-zA-Z]+)", text)

    if match:
        origin = match.group(1).capitalize()
        destination = match.group(2).capitalize()
        return origin, destination

    return None, None


def extract_date(text):

    import re

    text = text.lower()

    # tomorrow
    if "tomorrow" in text:
        return "tomorrow"

    # 20 May
    match1 = re.search(r"\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\b", text)

    if match1:
        return match1.group(0)

    # May 20
    match2 = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+\d{1,2}\b", text)

    if match2:
        return match2.group(0)

    return None