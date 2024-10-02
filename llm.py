import json
import PyPDF2
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

from cache import cache_request_get, affiliation_cache_manager, tldr_cache_manager, overview_cache_manager, \
    paper_review_cache_manager
from logos import ARXIV_LOGO, HF_LOGO, EMERGENTMIND_LOGO, X_LOGO, HACKERNEWS_LOGO, REDDIT_LOGO, \
    GITHUB_LOGO, YOUTUBE_LOGO

load_dotenv()


def get_author_affiliations(arxiv_url):
    arxiv_id = arxiv_url.split('/')[-1]
    cached_response = affiliation_cache_manager.get_cached_response(arxiv_id)
    if cached_response:
        return cached_response

    pdf_content = cache_request_get(arxiv_url, f"{arxiv_id}.pdf")
    pdf_content = BytesIO(pdf_content)
    # Extract text from the first two pages of the PDF
    pdf_reader = PyPDF2.PdfReader(pdf_content)
    text = ""
    for page in pdf_reader.pages[:2]:  # Only process the first two pages
        text += page.extract_text()

    # Initialize OpenAI client
    client = OpenAI()

    # Use GPT-4o mini to extract affiliations
    prompt = (
        "Extract the author affiliations from this arXiv paper text. "
        "Return only a json list of unique institutions."
        "The text is from the first two pages of the paper:\n\n"
        f"{text[:4000]}"  # Still limiting to 4000 characters as a precaution
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are an AI assistant that extracts author affiliations from academic papers."},
            {"role": "user", "content": prompt}
        ]
    )
    affiliations = response.choices[0].message.content
    affiliation_cache_manager.cache_response(arxiv_id, affiliations)
    return affiliations


def post_process(llm_result):
    str = llm_result.strip('`')
    str = str.replace('json', '', 1)
    str = str.strip()
    return '; '.join(json.loads(str))


def get_tldr(arxiv_id, title, abstract):
    cached_response = tldr_cache_manager.get_cached_response(arxiv_id)
    if cached_response:
        return cached_response

    client = OpenAI()

    prompt = (
        "Give a summary or tldr of a research paper given its title and abstract in three sentences or less."
        "\n\n"
        f"title: {title}\n"
        f"abstract: {abstract}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are an AI assistant that helps reading academic papers."},
            {"role": "user", "content": prompt}
        ]
    )

    tldr = response.choices[0].message.content
    tldr_cache_manager.cache_response(arxiv_id, tldr)
    return tldr


def format_overview(overview):
    overview = f"## Overview\n\n{overview}"
    return overview


def get_overview(last_monday, reviewed_papers):
    cached_response = overview_cache_manager.get_cached_response(last_monday)
    if cached_response:
        return format_overview(cached_response)

    client = OpenAI()

    prompt = (
        "Give an overview of papers given titles, abstracts, and notes in five sentences or less."
        "The overview should cover common topics across the papers."
        "Use professional language and style."
        "\n\n"
    )

    for i, paper in enumerate(reviewed_papers):
        prompt += f"paper {i + 1}:\n"
        prompt += f"title: {paper['title']}\n"
        prompt += f"abstract: {paper['tldr']}\n"
        prompt += f"notes: {paper['notes']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are an AI assistant that helps reading papers. Provide an overview of the papers."},
            {"role": "user", "content": prompt}
        ]
    )

    overview = response.choices[0].message.content
    overview_cache_manager.cache_response(last_monday, overview)

    return format_overview(overview)


def format_review(paper, review, picked, spreadsheet_id):
    arxiv_id = paper['arXiv'].split('/')[-1]
    content = ""
    if picked:
        content += f"""### Spotlight <span style="font-size: 24px;">&#x1F526;</span>"""
        content += "\n\n"

    content += f"**[{paper['title']}]({paper['arXivPdf']})**"
    content += "\n\n"

    content += f"_{paper['affiliations']}_\n\n"

    def make_logo_link(logo, link, tooltip):
        return f"""<a href="{link}" target="_blank" title="{tooltip}"><img src="{logo}"></a>"""

    def semantic_scholar_link(arxiv_id):
        return f"""<a href="https://api.semanticscholar.org/arXiv:{arxiv_id}" target="_blank" title="Semantic Scholar page"><img src="https://cdn.semanticscholar.org/838efdaeab2a7376/img/favicon-32x32.png" width="24" height="24"></a>"""

    def hf_link(paper):
        return f"""<a href="{paper['url']}" target="_blank" title="Hugging Face Papers"><span style="font-size: 24px;">&#x1F917;</span></a>"""

    def horizontal_space():
        return """&nbsp; &nbsp;"""

    def github_stats(paper):
        return paper['githubStarsCount'] if int(paper['githubReposCount']) > 0 else paper['githubPagesCount']

    def make_social_media_link(link, tooltip, count):
        # return f"""<span>{logo} {count}</span>"""
        return f"""<img src="{link}" alt="{tooltip}"><span>{count}</span>"""

    # links
    content += (
        f"<div style='display: flex; align-items: center; justify-content: center;'>"
        f"{make_logo_link(ARXIV_LOGO, paper['arXiv'], 'arXiv')}"
        f"{horizontal_space()}"
        f"{semantic_scholar_link(arxiv_id)}"
        f"{horizontal_space()}"
        # f"{make_logo_link(EMERGENTMIND_LOGO, f'https://www.emergentmind.com/papers/{arxiv_id}', 'Emergent Mind page')}"
        # f"{horizontal_space()}"
        # f" {make_logo_link(HF_LOGO, paper['url'], 'Hugging Face Papers')}"
        f"{hf_link(paper)}"
        f"{horizontal_space()}"
        f"{paper['upvote']}"
        # f"{horizontal_space()}"
        # f"{horizontal_space()}"
        # social media: X, HackerNews, Reddit, YouTube, GitHub
        # f"{make_social_media_link(X_LOGO, 'X', paper['twitterLikesCount'])}"
        # f"{horizontal_space()}"
        # f"{make_social_media_link(HACKERNEWS_LOGO, 'HackerNews', paper['hackerNewsPointsCount'])}"
        # f"{horizontal_space()}"
        # f"{make_social_media_link(REDDIT_LOGO, 'Reddit', paper['redditPointsCount'])}"
        # f"{horizontal_space()}"
        # f"{make_social_media_link(YOUTUBE_LOGO, 'YouTube', paper['youtubePaperMentionsCount'])}"
        # f"{horizontal_space()}"
        # f"{make_social_media_link(GITHUB_LOGO, 'GitHub', github_stats(paper))}"
        f"</div>"
        f"\n\n")

    def notes_cell_url(spreadsheet_id, row):
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid=0#gid=0&range=A{row}"

    content += (f"{review}"
                # f"""<a href="{notes_cell_url(spreadsheet_id, paper['row_index'])}" target="_blank"> Raw notes</a>"""
                "\n\n"
                f"<small>Raw notes: {paper['notes']}</small>"
                f"\n\n---\n\n")

    return content


def get_paper_review(paper, spreadsheet_id, picked=False):
    arxiv_id = paper['arXiv'].split('/')[-1]
    cached_response = paper_review_cache_manager.get_cached_response(arxiv_id)
    if cached_response:
        return format_review(paper, cached_response, picked, spreadsheet_id)

    client = OpenAI()

    num_sentences = "five" if picked else "three"

    prompt = (
        f"Give an paper's title, abstract, and notes, generate a review in {num_sentences} sentences or less. "
        "Do not include the title in the review, using 'this paper' is a replacement when needed."
        "Do not include the original abstract or notes in the review."
        "Use the first person pronouns (I) when appropriate."
        "Use a style that strikes a balance between professional and engaging and informal."
        "\n\n"
    )

    prompt += f"paper:\n"
    prompt += f"title: {paper['title']}\n"
    prompt += f"abstract: {paper['tldr']}\n"
    prompt += f"notes: {paper['notes']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are an AI assistant that helps reading papers. Provide an overview of the paper."},
            {"role": "user", "content": prompt}
        ]
    )

    review = response.choices[0].message.content
    paper_review_cache_manager.cache_response(arxiv_id, review)

    return format_review(paper, review, picked, spreadsheet_id)


if __name__ == '__main__':
    arxiv_url = 'https://arxiv.org/pdf/2408.08072'
    affiliations = get_author_affiliations(arxiv_url)
    affiliations = post_process(affiliations)
    print(affiliations)
