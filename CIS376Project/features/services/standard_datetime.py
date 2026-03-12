from datetime import datetime

def normalize_date(date_str):
    formats = [
        "%m-%d-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError("Invalid date format")

def normalize_time(time_str):
    formats = [
        "%H:%M",
        "%I:%M %p",
        "%I:%M%p",
        "%I:%M"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(time_str.strip(), fmt).strftime("%H:%M")
        except ValueError:
            pass
    raise ValueError("Invalid time format")

def format_service_datetime(service_date, service_time):  # idk if this format can be used for front end
    dt = datetime.strptime(f"{service_date} {service_time}", "%Y-%m-%d %H:%M")

    month = dt.month
    day = dt.day
    year = dt.strftime('%y')
    time = dt.strftime('%I:%M %p').lstrip('0')

    return f'{month}/{day}/{year}, {time}'