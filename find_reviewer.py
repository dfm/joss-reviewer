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


def _count(column: pd.Series, words: List[str]) -> pd.Series:
    pattern = "|".join(map("({0})".format, map(re.escape, words)))
    return (~column.str.extract(re.compile(pattern, re.I)).isnull()).sum(1)


def score_languages(
    reviewers: pd.DataFrame, languages: List[str]
) -> pd.Series:
    preferred = _count(reviewers["Preferred Programming Languages"], languages)
    other = _count(reviewers["Other Programming Languages"], languages)
    score = 10 * (preferred + 0.5 * other) / len(languages)
    return score


def score_keywords(reviewers: pd.DataFrame, keywords: List[str]) -> pd.Series:
    return (
        10
        * _count(
            reviewers["Domains/topic areas you are comfortable reviewing"],
            keywords,
        )
        / len(keywords)
    )


def score_reviewers(
    keywords: List[str], languages: List[str] = []
) -> pd.DataFrame:
    reviewers = get_reviewer_list()

    reviewers["keyword_score"] = score_keywords(reviewers, keywords)
    reviewers = reviewers[reviewers["keyword_score"] > 0]

    if len(languages):
        reviewers["language_score"] = score_languages(reviewers, languages)
        reviewers = reviewers[reviewers["language_score"] > 0]

    else:
        reviewers["language_score"] = np.zeros(len(reviewers))

    reviewers["total_score"] = (
        reviewers.keyword_score
        + 0.5 * reviewers.language_score
        - reviewers["Active reviews"]
    )

    return reviewers


def list_reviewers(
    keywords: List[str], languages: List[str] = [], count: int = 10
) -> pd.DataFrame:
    reviewers = score_reviewers(keywords, languages)
    subset = reviewers.sort_values(
        ["total_score", "random"], ascending=False
    ).head(count)
    for _, row in subset.iterrows():
        sys.stdout.write(
            "https://github.com/\033[1;31m{0.username}\033[0m:\n".format(row)
        )
        sys.stdout.write(
            "areas: {0}\n".format(
                row[
                    "Domains/topic areas you are comfortable reviewing"
                ].replace("\n", " "),
            )
        )
        sys.stdout.write(
            "languages: \033[1;30m{0}\033[0m / \033[1;30m{1}\033[0m\n".format(
                row["Preferred Programming Languages"].replace("\n", " "),
                row["Other Programming Languages"].replace("\n", " "),
            )
        )
        sys.stdout.write(
            "active: \033[1;32m{0:.0f}\033[0m /".format(row["Active reviews"])
        )
        sys.stdout.write(
            "all time: \033[1;32m{0:.0f}\033[0m /".format(
                row["Review count(all time)"]
            )
        )
        sys.stdout.write(
            "last year: \033[1;32m{0:.0f}\033[0m /".format(
                row["Review count(last year)"]
            )
        )
        sys.stdout.write(
            "last quarter: \033[1;32m{0:.0f}\033[0m \n\n".format(
                row["Review count(last quarter)"]
            )
        )


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
    args = parser.parse_args()

    list_reviewers(args.keywords, languages=args.language, count=args.num)
