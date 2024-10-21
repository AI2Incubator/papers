import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from emergentmind import get_stats
from llm import get_author_affiliations, post_process, get_tldr
from cache import hf_cache_manager, hfp_cache_manager


def fetch_huggingface_papers(url="https://huggingface.co/papers", paper_date='2024-08-12'):
    content = hf_cache_manager.get_cached_response(paper_date)
    if content is None:
        content = (requests.get(f"{url}?date={paper_date}")).text
        hf_cache_manager.cache_response(paper_date, content)

    soup = BeautifulSoup(content, 'html.parser')

    papers = []
    for paper in soup.select('div.from-gray-50-to-white'):
        title_element = paper.select_one('h3 a')
        title = title_element.text.strip()

        paper_id = title_element['href']
        hf_paper_url = urljoin(url, paper_id)
        arxiv_paper_id = paper_id.split('/')[-1]
        # print(arxiv_paper_id)

        # Get the last part of the relative_link for the cache filename
        # paper_content = cache_request_get(absolute_url, cache_filename)
        paper_content = hfp_cache_manager.get_cached_response(arxiv_paper_id)
        if paper_content is None:
            paper_content = (requests.get(hf_paper_url)).text
            hfp_cache_manager.cache_response(arxiv_paper_id, paper_content)

        paper_of_the_day = extract_href_with_text(paper_content, 'Paper of the day', silent=True)
        pdf_link = extract_href_with_text(paper_content, 'View PDF')

        abstract = extract_abstract(paper_content)
        tldr = get_tldr(arxiv_paper_id, title, abstract)
        # social_media_stats = get_stats(arxiv_paper_id)

        papers.append(dict(
            notes="",
            pick="",
            title=title,
            tldr=tldr,
            affiliations=post_process(get_author_affiliations(pdf_link)),
            upvote=extract_upvote_count(paper_content),
            paperOfTheDay=paper_date if paper_of_the_day else None,
            # **social_media_stats,
            abstract=abstract,
            date=paper_date,
            arXiv=extract_href_with_text(paper_content, 'View arXiv page'),
            url=hf_paper_url,
            arXivPdf=pdf_link
        ))

    return papers


def extract_abstract(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    abstract_header = soup.find('h2', string='Abstract')
    if abstract_header:
        # Get the next sibling element (which should be the paragraph containing the abstract)
        abstract_paragraph = abstract_header.find_next_sibling('p')
        if abstract_paragraph:
            return abstract_paragraph.get_text(strip=True).replace('\n', ' ')

    raise ValueError("Abstract not found in the given HTML content.")


def extract_href_with_text(html_content, text, silent=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    # link = soup.find('a', lambda x: text in x)
    link = soup.find(lambda tag: tag.name == 'a' and text in tag.get_text())
    if link:
        return link.get('href')
    elif silent:
        return None

    raise ValueError("arXiv link not found in the given HTML content.")


def extract_upvote_count(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    upvote_div = soup.find('div', class_='font-semibold text-orange-500')

    try:
        return int(upvote_div.text)
    except:
        return 0

#%%

# papers = fetch_huggingface_papers()
# column_names = list(papers[0].keys())
# paper_values = [list(paper.values()) for paper in papers]
