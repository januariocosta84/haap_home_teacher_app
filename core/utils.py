def normalize_whatsapp_number(value):
    """Normalize a WhatsApp/phone number to the stored +670XXXXXXXX format.

    Accepts input with or without the +670 country code (e.g. "77121173",
    "67077121173", "+67077121173") and returns the canonical "+670..." form,
    so lookups against User.whatsapp_number match regardless of how the
    user typed it.
    """
    if not value:
        return value

    value = value.strip().replace(' ', '').replace('-', '')

    if value.startswith('+670'):
        return value
    if value.startswith('670'):
        return '+' + value
    if value.startswith('+'):
        return value

    return '+670' + value
