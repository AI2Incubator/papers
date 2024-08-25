def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()

ARXIV_LOGO = read_file('./assets/arXiv.svg')
EMERGENTMIND_LOGO = read_file('assets/EmergentMind.svg')
GITHUB_LOGO = read_file('./assets/GitHub.svg')
HACKERNEWS_LOGO = read_file('./assets/HackerNews.svg')
REDDIT_LOGO = read_file('./assets/Reddit.svg')
YOUTUBE_LOGO = read_file('./assets/YouTube.svg')
X_LOGO = read_file('./assets/X.svg')

HF_LOGO = """<span style="font-size: 24px;">&#x1F917;</span>"""
