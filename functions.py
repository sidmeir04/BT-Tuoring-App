import datetime
lower_days = ['monday','tuesday','wednesday','thursday','friday']
def find_next_day_of_week(day_of_week):
    day_index = lower_days.index(day_of_week.lower())
    today = datetime.datetime.now().weekday()
    days_ahead = (day_index - today) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_day = datetime.datetime.now() + datetime.timedelta(days=days_ahead)

    return next_day.strftime("%Y-%m-%d")

print(find_next_day_of_week('wednesday'))