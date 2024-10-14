from datetime import datetime


def parse_timestamp(timestamp_str):
    try:
        s = timestamp_str.replace("-", "T", 1)
        s = s.replace(":", ".", 1)
        s = s.replace(".", "-", 1)
        s = s.replace(".", "-", 1)
        s = s.replace(".", ":", 1)
        s = s.replace(".", ":", 1)
        s += "Z"
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.timestamp() * 1000
    except Exception as e:
        print(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None


def format_timestamp(timestamp):
    total_seconds = int(int(timestamp) / 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}시간 {minutes}분 {seconds}초"
    elif minutes > 0:
        return f"{minutes}분 {seconds}초"
    else:
        return f"{seconds}초"
