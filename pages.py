#!/usr/bin/env python3
import html
import os
import re
import requests
import typing
# import xml.etree.ElementTree as ET

class Build(typing.NamedTuple):
    major: int
    minor: int
    beta:  int
    seq:   int

    @classmethod
    def from_title(cls, title):
        major, minor, seq, beta = re.search(r'\((\d+)([A-Z])(\d+)([a-z])?\)', title).groups()
        major = int(major)
        minor = ord(minor) - ord('A')
        seq   = int(seq)
        beta  = ord(beta) - ord('a') + 1 if beta else 27
        return cls(major, minor, beta, seq)

def get_releases(repo, token=None):
    releases = []
    headers = {'Authorization': f'token {token}'} if token else None
    url = f'https://api.github.com/repos/{repo}/releases'
    while 1:
        rsp = requests.get(url=url, headers=headers, allow_redirects=False)
        assert rsp.status_code == 200
        releases.extend(rsp.json())
        if 'next' not in rsp.links:
            break
        url = rsp.links['next']['url']
    return releases

def dedup(releases):
    collections = {}
    for release in releases:
        collections.setdefault(release['name'], []).append((
            (release['body'] or '').strip('`'),
            release['tag_name'],
            release['html_url'],
        ))
    return collections

def main():
    releases = get_releases(
        'zhangyoufu/macOS',
        token=os.environ['GITHUB_TOKEN'],
    )
    collections = sorted(dedup(releases).items(),
        key=lambda item: Build.from_title(item[0]),
        reverse=True,
    )

    print('''\
<!DOCTYPE html>
<head>
  <title>macOS Installer Archive</title>
  <style>
.collection + .collection {
  margin-top: 1em;
}

.monospace {
  font-family: monospace;
}
  </style>
</head>
<body>''')
    for title, releases in collections:
        print('  <div class="collection">')
        print(f'    <strong>{html.escape(title)}</strong>')
        for date, tag, url in sorted(releases):
            print(f'    <div>')
            print(f'      <a class="monospace" href="{html.escape(url)}">{html.escape(tag)}</a>')
            print(f'      <span class="monospace">{html.escape(date)}</span>')
            print(f'    </div>')
        print('  </div>')
        print('</body>')
        print('</html>')

if __name__ == '__main__':
    main()