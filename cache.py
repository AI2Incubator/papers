import base64
import functools
import gzip
import json
import time
from pathlib import Path

import requests

def cache_dir():
    return Path('./.cache')

def text_compress(str):
    data = gzip.compress(str.encode('utf-8'))
    return base64.b64encode(data).decode('ascii')

def text_decompress(str):
    data = base64.b64decode(str.encode('ascii'))
    return gzip.decompress(data).decode('utf-8')


def cache_result(cache_filename):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_dir = Path.cwd()/ '.cache'
            cache_file = cache_dir / cache_filename

            # Check if cache exists and is fresh
            if cache_file.exists():
                with cache_file.open('rb') as f:
                    cache = f.read()
                return cache

            # If cache doesn't exist or is stale, call the function
            result = func(*args, **kwargs)

            # Update cache
            with cache_file.open('wb') as f:
                f.write(result)

            return result
        return wrapper

    return decorator


def cache_request_get(url, cache_filename):
    @cache_result(cache_filename=cache_filename)
    def do_work():
        return (requests.get(url)).content

    return do_work()


class CacheManager:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        cache = {}
        if self.cache_file.exists():
            with self.cache_file.open("r") as f:
                for line in f:
                    entry = json.loads(line)
                    cache[entry["key"]] = text_decompress(entry["response"])
        return cache

    def get_cached_response(self, cache_key):
        return self.cache.get(cache_key)

    def cache_response(self, cache_key, response):
        self.cache[cache_key] = response
        with self.cache_file.open("a") as f:
            entry = {"key": cache_key, "response": text_compress(response)}
            f.write(json.dumps(entry) + "\n")


HF_CACHE_FILE = Path("./.cache/hf_cache.jsonl")
hf_cache_manager = CacheManager(HF_CACHE_FILE)

HFP_CACHE_FILE = Path("./.cache/hfp_cache.jsonl")
hfp_cache_manager = CacheManager(HFP_CACHE_FILE)

TLDR_CACHE_FILE = Path("./.cache/affiliation_cache.jsonl")
affiliation_cache_manager = CacheManager(TLDR_CACHE_FILE)

TLDR_CACHE_FILE = Path("./.cache/tldr_cache.jsonl")
tldr_cache_manager = CacheManager(TLDR_CACHE_FILE)

def initialize_cache_and_gitignore():
    cache_dir().mkdir(exist_ok=True)

    gitignore_path = Path('./.gitignore')
    if not gitignore_path.exists():
        gitignore_path.touch()

    # Read the content
    with gitignore_path.open('r') as gitignore:
        content = gitignore.read()

    # Append if necessary
    if '.cache/' not in content:
        with gitignore_path.open('a') as gitignore:
            gitignore.write('\n.cache/\n')

