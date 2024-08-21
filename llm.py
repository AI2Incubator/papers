import json
import PyPDF2
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

from cache import cache_request_get, affiliation_cache_manager, tldr_cache_manager

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


if __name__ == '__main__':
    arxiv_url = 'https://arxiv.org/pdf/2408.08072'
    affiliations = get_author_affiliations(arxiv_url)
    affiliations = post_process(affiliations)
    print(affiliations)
