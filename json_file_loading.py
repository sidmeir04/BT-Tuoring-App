import json
from datetime import time, datetime, timedelta
from calendar import weekday

user_type_key = {0:'student', 1:'teacher', 2:'administrator', 3:'developer'}

def load_basic_json_file():
    with open('static/assets/basic_json_file.json', 'r') as file:
        basic = json.load(file)
    return basic

def load_default_schedule():
    with open('static/assets/default_schedule.json', 'r') as file:
        default_schedule = json.load(file)
    return default_schedule

def load_default_notifactions():
    with open('static/assets/default_notifactions.json', 'r') as file:
        default_notifactions = json.load(file)
    return default_notifactions

def load_non_basic_json_file():
    with open('static/assets/messages.json', 'r') as file:
        default_schedule = json.load(file)
    return default_schedule

def string_to_time(time_str):
    hour, minute = map(int, time_str.split(':'))
    # Create a time object with the provided hour and minute
    result_time = time(hour=hour, minute=minute)
    return result_time

lower_days = ['monday','tuesday','wednesday','thursday','friday']
def find_next_day_of_week(day_of_week):
    day_index = lower_days.index(day_of_week.lower())
    today = datetime.now().weekday()
    days_ahead = (day_index - today) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_day = datetime.now() + timedelta(days=days_ahead)
    # returns the date of the next time a day of the week would occur
    return next_day.strftime("%Y-%m-%d")


def time_to_min(time):
    return sum(i*j for i, j in zip(map(int, time.split(':')), (60, 1, 1/60)))

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
def date_to_day(date):
    year, month, day = (int(i) for i in date.split('-'))
    dayNumber = weekday(year, month, day)
    day = days[dayNumber].lower()
    return day