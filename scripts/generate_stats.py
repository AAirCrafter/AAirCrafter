import os
from collections import defaultdict

import requests

USERNAME = "AAirCrafter"
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}

COLORS = ["#70a5fd", "#bf91f3", "#38bdae", "#f7768e", "#e0af68", "#9ece6a"]


def get_all_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def get_commit_count():
    r = requests.get(
        "https://api.github.com/search/commits",
        headers={**HEADERS, "Accept": "application/vnd.github.cloak-preview+json"},
        params={"q": f"author:{USERNAME}"},
    )
    r.raise_for_status()
    return r.json().get("total_count", 0)


def get_languages(repos):
    lang_bytes = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        r = requests.get(repo["languages_url"], headers=HEADERS)
        if r.status_code != 200:
            continue
        for lang, count in r.json().items():
            lang_bytes[lang] += count
    return lang_bytes


def get_most_active_repos(repos, limit=4):
    owned = [r for r in repos if not r.get("fork")]
    return sorted(owned, key=lambda r: r["pushed_at"], reverse=True)[:limit]


def write_overview_svg(repos, stars, commits, path):
    rows = [("Repos", repos), ("Commits", commits), ("Stars", stars)]
    height = 60 + len(rows) * 30
    svg = f'''<svg width="380" height="{height}" viewBox="0 0 380 {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #1a1b27; }}
    .title {{ font: 600 16px 'Segoe UI', sans-serif; fill: #70a5fd; }}
    .label {{ font: 400 14px 'Segoe UI', sans-serif; fill: #38bdae; }}
    .value {{ font: 600 14px 'Segoe UI', sans-serif; fill: #b0bfff; }}
  </style>
  <rect class="bg" x="0.5" y="0.5" rx="8" width="379" height="{height - 1}" stroke="#2e2f3e" />
  <text x="20" y="35" class="title">{USERNAME}'s GitHub Stats</text>
'''
    y = 65
    for label, value in rows:
        svg += f'  <text x="20" y="{y}" class="label">{label}:</text>\n'
        svg += f'  <text x="200" y="{y}" class="value">{value}</text>\n'
        y += 30
    svg += "</svg>"
    with open(path, "w") as f:
        f.write(svg)


def write_languages_svg(langs, path):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:6]
    height = 60 + len(top) * 40
    svg = f'''<svg width="380" height="{height}" viewBox="0 0 380 {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #1a1b27; }}
    .title {{ font: 600 16px 'Segoe UI', sans-serif; fill: #70a5fd; }}
    .label {{ font: 400 13px 'Segoe UI', sans-serif; fill: #b0bfff; }}
  </style>
  <rect class="bg" x="0.5" y="0.5" rx="8" width="379" height="{height - 1}" stroke="#2e2f3e" />
  <text x="20" y="35" class="title">Most Used Languages</text>
'''
    y = 55
    for i, (lang, count) in enumerate(top):
        pct = round(count / total * 100, 1)
        bar_width = max(int(pct * 2.8), 3)
        color = COLORS[i % len(COLORS)]
        svg += f'  <text x="20" y="{y + 14}" class="label">{lang} - {pct}%</text>\n'
        svg += f'  <rect x="20" y="{y + 22}" width="{bar_width}" height="6" rx="3" fill="{color}" />\n'
        y += 40
    svg += "</svg>"
    with open(path, "w") as f:
        f.write(svg)


def write_active_repos_svg(repos, path):
    height = 60 + len(repos) * 34
    svg = f'''<svg width="380" height="{height}" viewBox="0 0 380 {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #1a1b27; }}
    .title {{ font: 600 16px 'Segoe UI', sans-serif; fill: #70a5fd; }}
    .name {{ font: 600 14px 'Segoe UI', sans-serif; fill: #b0bfff; }}
    .meta {{ font: 400 12px 'Segoe UI', sans-serif; fill: #38bdae; }}
  </style>
  <rect class="bg" x="0.5" y="0.5" rx="8" width="379" height="{height - 1}" stroke="#2e2f3e" />
  <text x="20" y="35" class="title">Most Active Projects</text>
'''
    y = 60
    for repo in repos:
        name = repo["name"]
        lang = repo.get("language") or "-"
        stars = repo.get("stargazers_count", 0)
        svg += f'  <text x="20" y="{y}" class="name">{name}</text>\n'
        svg += f'  <text x="20" y="{y + 16}" class="meta">{lang} - ★ {stars}</text>\n'
        y += 34
    svg += "</svg>"
    with open(path, "w") as f:
        f.write(svg)


def main():
    os.makedirs("generated", exist_ok=True)
    repos = get_all_repos()
    owned = [r for r in repos if not r.get("fork")]

    total_repos = len(owned)
    total_stars = sum(r.get("stargazers_count", 0) for r in owned)
    commit_count = get_commit_count()
    langs = get_languages(owned)
    active = get_most_active_repos(repos)

    write_overview_svg(total_repos, total_stars, commit_count, "generated/overview.svg")
    write_languages_svg(langs, "generated/languages.svg")
    write_active_repos_svg(active, "generated/active_repos.svg")


if __name__ == "__main__":
    main()
