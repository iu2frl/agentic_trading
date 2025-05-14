from datetime import datetime, timedelta
import json

class Color:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

def load_file(file_path):
    ext = file_path.split(".")[-1]
    data = None
    with open(file_path, "r") as f:
        if ext == 'json':
            data = json.load(f)
        elif ext == "txt":
            data = f.read()

    return data
        
def write_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
        
def get_date_range(reference_date=None, month_diff=3):
    if reference_date is None:
        reference_date = datetime.today().date()  # Default to today's date
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
    
    # Calculate 'month_diff' months back
    start_date = reference_date.replace(day=1)  # Move to the first day of the month
    for _ in range(month_diff):
        start_date = (start_date - timedelta(days=1)).replace(day=1)  # Move back one month
    
    return start_date.strftime("%Y-%m-%d"), reference_date.strftime("%Y-%m-%d")

# start_date, end_date = get_date_range()
# technical_start_date , technical_end_date = get_date_range(month_diff=5)