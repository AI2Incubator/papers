from datetime import datetime, timedelta
from pathlib import Path


def read_tsv(file_name):
    with open(file_name, 'r') as f:
        lines = f.readlines()
    return [line.strip().split('\t') for line in lines]


def append_tsv(file_name, values):
    with open(file_name, 'a') as f:
        f.write('\t'.join(values) + '\n')


def read_tsv_dict(file_name):
    # use pathlib, touch file if it does not exist
    Path(file_name).touch()
    lines = read_tsv(file_name)
    return {line[0]: line[1] for line in lines}


def get_last_monday():
    today = datetime.today()
    run_date = today
    if run_date.weekday() != 0:  # Monday is represented by 0
        print(f"Today is {run_date}")
        run_date = run_date - timedelta(days=run_date.weekday())
        print(f"Running as Monday ({run_date})")
    last_week = [run_date - timedelta(days=7 - i) for i in range(5)]
    days = [day.strftime('%Y-%m-%d') for day in last_week]
    last_monday = days[0]
    return days, last_monday


def full_url(spreadsheet_id):
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
