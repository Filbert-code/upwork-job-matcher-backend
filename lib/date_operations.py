from datetime import datetime, timedelta


def convert_posted_time_to_datetime(posted_time: str):
    time_posted_split = posted_time.split(' ')
    if time_posted_split[1] == 'second' or time_posted_split[1] == 'seconds':
        return datetime.now() - timedelta(seconds=int(time_posted_split[0]))
    elif time_posted_split[1] == 'minute' or time_posted_split[1] == 'minutes':
        return datetime.now() - timedelta(minutes=int(time_posted_split[0]))
    elif time_posted_split[1] == 'hour' or time_posted_split[1] == 'hours':
        return datetime.now() - timedelta(hours=int(time_posted_split[0]))
    elif time_posted_split[1] == 'day' or time_posted_split[1] == 'days':
        return datetime.now() - timedelta(days=int(time_posted_split[0]))
    elif time_posted_split[1] == 'week' or time_posted_split[1] == 'weeks':
        return datetime.now() - timedelta(weeks=int(time_posted_split[0]))