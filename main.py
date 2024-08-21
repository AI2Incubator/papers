from datetime import datetime, timedelta

from gsheet import GSheet
from process import fetch_huggingface_papers

def run():
    today = datetime.today()
    run_date = today
    if run_date.weekday() != 0:  # Monday is represented by 0
        print(f"Today is {run_date}")
        run_date = run_date - timedelta(days=run_date.weekday())
        print(f"Running as Monday ({run_date})")

    last_week = [run_date - timedelta(days=7-i) for i in range(5)]
    days = [day.strftime('%Y-%m-%d') for day in last_week]
    last_monday = days[0]

    papers = []
    for day in days:
        print(f"Processing papers for date: {day}")
        day_papers = fetch_huggingface_papers(paper_date=day)
        papers.extend(day_papers)

    papers = sorted(papers, key=lambda x: x['upvote'], reverse=True)

    spreadsheet_name = f"Paper Review: {last_monday}"
    gsheet = GSheet(papers, spreadsheet_name)
    spreadsheet_id = gsheet.create_spreadsheet()

    gsheet.insert_clickable_urls(gsheet.titles, gsheet.pdf_urls)

    gsheet.insert_notes(gsheet.abstracts, 'tldr')

    gsheet.wrap_text_in_columns(['notes', 'title', 'tldr', 'affiliations'], "WRAP")

    gsheet.set_cell_dims(['notes', 'title', 'tldr', 'affiliations'], [400, 200, 500, 200], dim='COLUMNS')

    # gsheet.make_sheet_public()

    print(f"Spreadsheet titled {spreadsheet_name} created: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

if __name__ == '__main__':
    run()
