import argparse
from datetime import datetime

from gsheet import GSheet, GSheetReader
from llm import get_overview, get_paper_review
from process import fetch_huggingface_papers
from utils import append_tsv, read_tsv_dict, get_last_monday, full_url

SPREADSHEET_FILE = './.data/spreadsheets.tsv'


def review_file(day):
    return f"./.data/review-{day}.md"

def retrieve_papers():
    days, last_monday = get_last_monday()

    spreadsheets = read_tsv_dict(SPREADSHEET_FILE)
    if last_monday in spreadsheets:
        print(f"Spreadsheet for {last_monday} already exists: {spreadsheets[last_monday]}")
        return

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

    print(f"Spreadsheet titled {spreadsheet_name} created: {full_url(spreadsheet_id)}")
    append_tsv(SPREADSHEET_FILE, [last_monday, spreadsheet_id])


def generate_review_aux(picked_papers, reviewed_papers, last_monday, spreadsheet_id):
    # pick the first paper from the picked_papers list
    print(f"Picked paper: {picked_papers[0]['title']}")
    picked_paper_short_title = input("Enter the short title for the picked paper: ")

    # convert last_monday which has format 'YYYY-MM-DD' to 'M/D/YYYY'
    date_obj = datetime.strptime(last_monday, '%Y-%m-%d')
    new_date = date_obj.strftime('%-m/%-d/%Y')

    title = f"Weekly paper roundup: {picked_paper_short_title} ({new_date})"
    print(title)

    over_view = get_overview(last_monday, reviewed_papers)
    content = f"# {title}\n\n{over_view}\n\n"

    for picked_paper in picked_papers:
        picked_paper_review = get_paper_review(picked_paper, spreadsheet_id, picked=True)
        content += f"{picked_paper_review}\n\n"

    content += "## Other papers\n\n"

    picked_paper_arxivids = [paper['arXiv'] for paper in picked_papers]
    for paper in reviewed_papers:
        if paper['arXiv'] in picked_paper_arxivids:
            continue
        content += get_paper_review(paper, spreadsheet_id)

    content += ("\n\n"
                "### Acknowledgements\n\n"
                "Papers are retrieved from [Hugging Face](https://huggingface.co/papers).\n\n"
                "Social media metrics are from [Emergent Mind](https://www.emergentmind.com/).\n\n")


    with open(review_file(last_monday), 'w') as f:
        f.write(content)
    return content


def generate_review():
    days, last_monday = get_last_monday()

    spreadsheets = read_tsv_dict(SPREADSHEET_FILE)
    if last_monday not in spreadsheets:
        print(f"Spreadsheet for {last_monday} does not exists")
        return

    spreadsheet_id = spreadsheets[last_monday]

    # read the spreadsheet from its URL using google api
    papers = GSheetReader(spreadsheet_id).read_sheet()

    for i, paper in enumerate(papers):
        paper['row_index'] = i + 2

    # find the paper where the pick column is non-empty
    picked_papers = []
    for paper in papers:
        if paper['pick']:
            picked_papers.append(paper)

    # find papers where the notes column is non-empty and not equal to 'skip', case insensitive
    reviewed_papers = [paper for paper in papers if paper['notes'] and paper['notes'].strip().lower() != 'skip']

    # sort reviewed_papers by the upvote column in descending order
    reviewed_papers = sorted(reviewed_papers, key=lambda x: int(x['upvote']), reverse=True)
    generate_review_aux(picked_papers, reviewed_papers, last_monday, spreadsheet_id)


def publish_review():
    pass


if __name__ == '__main__':
    # run()
    parser = argparse.ArgumentParser(description="Process papers with three modes: retrieve, review, and publish.")
    parser.add_argument("mode", choices=["retrieve", "review", "publish"], help="Mode of operation")
    args = parser.parse_args()

    if args.mode == "retrieve":
        retrieve_papers()
    elif args.mode == "review":
        generate_review()
    elif args.mode == "publish":
        publish_review()

#%%