import json
from datetime import time, datetime, timedelta
from calendar import weekday
from PIL import Image



user_type_key = {0:'student', 1:'teacher', 2:'administrator', 3:'developer'}

def load_session_history_JSON():
    with open('static/assets/session_history_JSON.json', 'r') as file:
        form = json.load(file)
    return form

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
def find_next_day_of_week(day_of_week : str):
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

def load_available_classes():
    with open('static/assets/store_classlist.json', 'r') as file:
        form = json.load(file)
    return form["class_list"]

def write_available_classes(classList):
    with open('static/assets/store_classlist.json', 'r') as file:
        classList = json.dumps(classList,indent=2)
        file.write(classList)
    return


def current_classlist():
    return {i:0 for i in UNIVERSAL_CLASSLIST}

def make_square(image, size):
    width, height = image.size
    new_dim = min(width, height)

    left = (width - new_dim) / 2
    top = (height - new_dim) / 2
    right = (width + new_dim) / 2
    bottom = (height + new_dim) / 2

    img_cropped = image.crop((left, top, right, bottom))
    img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

    return img_resized

def count_weekdays_between(start_date: datetime, end_date: datetime, weekday: int) -> int:

    # start_date = start_date.date()
    end_date = end_date.date()

    current_date = start_date
    weekday_count = 0
    
    while current_date <= end_date:
        if current_date.weekday() == weekday:
            weekday_count += 1
        current_date += timedelta(days=1)
    
    return weekday_count

def load_student_teacher_JSON():
    with open('static/assets/student_teacher.json', 'r') as file:
        student_teacher_file = json.load(file)
    return student_teacher_file


days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
def find_next_day(selected_days):
    days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    current_day = datetime.today().weekday()
    
    # Loop through the days in order, starting from the day after the current day
    for i in range(7):
        day_index = (current_day + 1 + i) % 7  # Wrap around the week using modulo
        if selected_days[day_index] == '1':
            return days_list[day_index]
        


from datetime import datetime, timedelta, time

def time_difference(time1, time2):
    """
    Calculates the time difference between two datetime.time objects.
    
    Arguments:
    - time1, time2: Both should be of type datetime.time.
    
    Returns:
    The difference as a timedelta object and as total seconds.
    """
    # Convert time objects to datetime objects on the same arbitrary date
    today = datetime.today()  # Use today's date to create full datetime objects
    dt1 = datetime.combine(today, time1)
    dt2 = datetime.combine(today, time2)
    
    # Find the difference between the two datetime objects
    diff = dt2 - dt1
    
    # Handle cases where time2 is earlier than time1 (time crossing midnight)
    if diff < timedelta(0):
        diff += timedelta(days=1)
    
    # Return the timedelta object and total seconds
    return diff.total_seconds() / 3600

def convert_date(date):
    if type(date) == str:
        date = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date.strftime("%b %-d")
    return formatted_date

PERIOD_TIMES = [("10:30","11:15"),("11:15","11:56"),("12:00","12:41"),("12:45","13:26")]

def next_weekday_date(day_name):
    # Mapping of day names to weekday numbers (0=Monday, 6=Sunday)
    days_of_week = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    
    # Get today's date and weekday
    today = datetime.now()
    today_weekday = today.weekday()
    
    # Get target weekday number for the given day name
    target_weekday = days_of_week.get(day_name.lower())
    if target_weekday is None:
        raise ValueError("Invalid day name. Use a valid day of the week in lowercase.")
    
    # Calculate days until the next occurrence of the target weekday
    days_until = (target_weekday - today_weekday + 7) % 7
    days_until = days_until if days_until != 0 else 7  # Skip to the next week if today is the target day

    # Get the next date of the target weekday
    next_date = today + timedelta(days=days_until)
    return next_date.date()