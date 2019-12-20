#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from typing import List

import requests
import numpy as np
import pandas as pd


SHEET_URL = "https://docs.google.com/spreadsheets/d/{0}/export?format=csv"
SHEET_URL = SHEET_URL.format("1PAPRJ63yq9aPC1COLjaQp8mHmEq3rZUzwUYxTulyu78")
CACHE_FILE = os.path.abspath("cache.csv")


def read_reviewer_list() -> pd.DataFrame:
    reviewers = pd.read_csv(CACHE_FILE, skiprows=1)
    reviewers["random"] = np.random.rand(len(reviewers))
    return reviewers


def get_reviewer_list(
    cache: bool = True, save_cache: bool = True
) -> pd.DataFrame:
    try:
        stat = os.stat(CACHE_FILE)
    except FileNotFoundError:
        pass
    else:
        delta = time.time() - stat.st_mtime
        if delta < 60 * 60:
            return read_reviewer_list()

    r = requests.get(SHEET_URL)
    r.raise_for_status()
    with open(CACHE_FILE, "wb") as f:
        f.write(r.content)
    return read_reviewer_list()


def _count(column: pd.Series, pattern: str) -> pd.Series:
    return (
        (~column.str.extractall(re.compile(pattern, re.I)).isnull())
        .sum(level=0)
        .sum(axis=1)
    )


def language_score(
    reviewers: pd.DataFrame, languages: List[str]
) -> pd.DataFrame:
    pattern = "|".join(
        map(
            r"([^a-zA-Z\+\#]{0}[^a-zA-Z\+\#])".format,
            map(re.escape, languages),
        )
    )
    reviewers["language_score"] = np.zeros(len(reviewers))
    score = _count(reviewers["Preferred Programming Languages"], pattern)
    reviewers.loc[score.index, "language_score"] += score
    score = 0.5 * _count(reviewers["Other Programming Languages"], pattern)
    reviewers.loc[score.index, "language_score"] += score
    return reviewers


def keyword_score(
    reviewers: pd.DataFrame, keywords: List[str]
) -> pd.DataFrame:
    pattern = "|".join(map(r"({0})".format, map(re.escape, keywords)))
    reviewers["keyword_score"] = np.zeros(len(reviewers))
    reviewers["keyword_score"] += _count(
        reviewers["Domains/topic areas you are comfortable reviewing"],
        pattern,
    )
    return reviewers


def score_reviewers(
    keywords: List[str], languages: List[str] = []
) -> pd.DataFrame:
    reviewers = get_reviewer_list()

    reviewers = keyword_score(reviewers, keywords)
    reviewers = reviewers[reviewers["keyword_score"] > 0]
    reviewers = language_score(reviewers, languages)
    reviewers = reviewers[reviewers["language_score"] > 0]

    norm = len(keywords) + 0.5 * len(languages)
    reviewers["total_score"] = (
        10 * (reviewers.keyword_score + 0.5 * reviewers.language_score) / norm
        - reviewers["Active reviews"]
    )
    reviewers.total_score /= reviewers.total_score.max()

    return reviewers


def get_github_info(user: str) -> dict:
    key = os.environ.get("GITHUB_API_KEY", None)
    if key is None:
        return None
    headers = {"Authorization": "Bearer {0}".format(key)}
    query = """
{{
    user(login: "{0}") {{
        name
        bio
        itemShowcase {{
            items(first: 3) {{
                edges {{
                    node {{
                        ... on Repository {{
                            name
                            description
                            primaryLanguage {{
                                name
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
    """.format(
        user
    )
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=headers,
    )
    r.raise_for_status()
    result = r.json()
    return result


def list_reviewers(
    keywords: List[str],
    languages: List[str] = [],
    count: int = 10,
    use_github: bool = True,
) -> None:
    reviewers = score_reviewers(keywords, languages)
    subset = reviewers.sort_values(
        ["total_score", "random"], ascending=False
    ).head(count)
    for i, (_, row) in enumerate(subset.iterrows()):
        if i:
            sys.stdout.write("\n---------------------\n\n")
        sys.stdout.write(
            "https://github.com/\033[1;31m{0.username}\033[0m:".format(row)
        )
        sys.stdout.write(" / score: {0:.3f}\n".format(row["total_score"]))
        sys.stdout.write(
            "areas: {0}\n".format(
                row[
                    "Domains/topic areas you are comfortable reviewing"
                ].replace("\n", " "),
            )
        )
        sys.stdout.write(
            "languages: \033[1;30m{0}\033[0m".format(
                row["Preferred Programming Languages"].replace("\n", " "),
            )
        )
        try:
            sys.stdout.write(
                " / \033[1;30m{0}\033[0m".format(
                    row["Other Programming Languages"].replace("\n", " "),
                )
            )
        except AttributeError:
            pass
        sys.stdout.write(
            "\nactive: \033[1;32m{0:.0f}\033[0m / ".format(
                row["Active reviews"]
            )
        )
        sys.stdout.write(
            "all time: \033[1;32m{0:.0f}\033[0m / ".format(
                row["Review count(all time)"]
            )
        )
        sys.stdout.write(
            "last year: \033[1;32m{0:.0f}\033[0m / ".format(
                row["Review count(last year)"]
            )
        )
        sys.stdout.write(
            "last quarter: \033[1;32m{0:.0f}\033[0m \n".format(
                row["Review count(last quarter)"]
            )
        )

        if not use_github:
            continue
        gh_info = get_github_info(row.username)
        if gh_info is None:
            continue
        user_info = gh_info.get("data", {}).get("user", {})
        bio = user_info.get("bio", None)
        if bio is not None:
            sys.stdout.write(
                "bio: {0}\n".format(bio.replace("\n", " ").replace("\r", ""))
            )
        repos = (
            user_info.get("itemShowcase", {}).get("items", {}).get("edges", [])
        )
        if len(repos):
            sys.stdout.write("repos:\n")
            for repo in repos:
                node = repo.get("node", {})
                name = node.get("name", None)
                if name is None:
                    continue
                sys.stdout.write("  {0}".format(name))
                lang = node.get("primaryLanguage", {})
                if lang is not None and lang.get("name", None) is not None:
                    sys.stdout.write(" ({0})".format(lang.get("name")))
                desc = node.get("description", None)
                if desc is not None:
                    sys.stdout.write(": {0}".format(desc))
                sys.stdout.write("\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find me some reviewers!")
    parser.add_argument(
        "keywords", nargs="+", help="Keywords to compare against"
    )
    parser.add_argument(
        "-l",
        "--language",
        action="append",
        help="The needed programming languages",
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=10,
        help="The number of reviewers to suggest",
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Don't list info from GitHub API",
    )
    args = parser.parse_args()

    list_reviewers(
        args.keywords,
        languages=args.language,
        count=args.num,
        use_github=not args.no_github,
    )
