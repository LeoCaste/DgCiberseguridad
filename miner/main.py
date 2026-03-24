import os
import time
import requests
import ast
import re
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def split_words(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    words = name.replace('-', '_').split('_')
    return [w.lower() for w in words if w and len(w) > 1]

def process_python(code):
    words = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                words.extend(split_words(node.name))
    except Exception:
        pass
    return words

def process_java(code):
    words = []
    pattern = re.compile(r'\b(?:public|protected|private|static|final)?\s+(?:[\w<>\[\]]+\s+)+(\w+)\s*\(')
    matches = pattern.findall(code)
    for match in matches:
        if match not in ['if', 'for', 'while', 'switch', 'catch']:
            words.extend(split_words(match))
    return words

def mine_github():
    languages = ["python", "java"]
    for lang in languages:
        url = f"https://api.github.com/search/repositories?q=language:{lang}&sort=stars&order=desc"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            time.sleep(10)
            continue
            
        repos = response.json().get("items", [])
        for repo in repos:
            repo_name = repo["full_name"]
            branch = repo["default_branch"]
            tree_url = f"https://api.github.com/repos/{repo_name}/git/trees/{branch}?recursive=1"
            
            tree_res = requests.get(tree_url, headers=HEADERS)
            if tree_res.status_code != 200:
                continue
                
            tree = tree_res.json().get("tree", [])
            ext = ".py" if lang == "python" else ".java"
            files = [f["path"] for f in tree if f["path"].endswith(ext)]
            
            for file_path in files[:5]: 
                raw_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
                raw_res = requests.get(raw_url)
                
                if raw_res.status_code == 200:
                    code = raw_res.text
                    extracted = process_python(code) if lang == "python" else process_java(code)
                        
                    for word in extracted:
                        r.zincrby("word_ranking", 1, word)
                        r.zincrby(f"word_ranking_{lang}", 1, word)
            
            time.sleep(2)

if __name__ == "__main__":
    while True:
        try:
            mine_github()
        except Exception as e:
            time.sleep(10)
        time.sleep(60)