def format_list(events, prefix, field_name):
    events = list(events)
    if len(events) == 0:
        return f"**Empty {field_name}**"
    else:
        return "\n".join([f"#{prefix}{i+1} {event}" for i, event in enumerate(events)])
