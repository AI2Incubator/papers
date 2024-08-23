from marshal import loads
from pathlib import Path
import re
import requests

from cache import CacheManager

def extract_value(input_string, key):
    pattern = rf'"{key}":\s*([^"]*),'
    match = re.search(pattern, input_string)
    if match:
        return int(match.group(1))
    return -1

def python_to_java_name(python_name):
    words = python_name.split('_')
    java_name = words[0].lower()
    for word in words[1:]:
        java_name += word.capitalize()
    return java_name

def paper_url(arxiv_id):
    return f"{EMERGENT_BASE_URL}{arxiv_id}"


EMERGENT_BASE_URL = 'https://www.emergentmind.com/papers/'
EMERGENT_CACHE = CacheManager(Path('.cache/emergent.json'), loads)

def get_stats(arxiv_id):
    stats = EMERGENT_CACHE.get_cached_response(arxiv_id)
    if stats:
        return stats

    content = (requests.get(paper_url(arxiv_id))).text.replace('&quot;', '"')
    stat_names = ["twitter_likes_count", "reddit_points_count", "hacker_news_points_count", "github_repos_count", "github_stars_count"]
    stats = { python_to_java_name(x): extract_value(content, x) for x in stat_names}
    EMERGENT_CACHE.cache_response(arxiv_id, stats)
    return stats



# %%

# stats = get_stats('2408.06292')

d = dict(a=1, b=2)
d2 = dict(c=3, d=4, **d, e=5)



