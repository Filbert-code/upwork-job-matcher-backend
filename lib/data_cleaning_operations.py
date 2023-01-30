def get_min_max_hourly_rates(hourly_rates_string: str):
    hourly_rates = hourly_rates_string.replace('Hourly: ', '').replace('$', '').split('-')
    if len(hourly_rates) == 1:
        return int(float(hourly_rates[0])), int(float(hourly_rates[0]))
    return int(float(hourly_rates[0])), int(float(hourly_rates[1]))
