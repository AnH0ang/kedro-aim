"""Labels PRs based on title.

Must be run in a github action with the pull_request_target event.
"""
import json
import os
import re

from github import Github  # type: ignore

context_dict = json.loads(os.getenv("CONTEXT_GITHUB"))  # type: ignore

repo = context_dict["repository"]
g = Github(context_dict["token"])
repo = g.get_repo(repo)
pr_number = context_dict["event"]["number"]
issue = repo.get_issue(number=pr_number)
title = issue.title


regex_to_labels = [
    (r"feat", "Feature"),
    (r"fix", "Bug Fix"),
    (r"docs", "Documentation"),
    (r"style", "Style"),
    (r"refactor", "Refactoring"),
    (r"perf", "Performance Improvement"),
    (r"test", "Testing"),
    (r"ci", "CI"),
]

labels_to_add = [label for regex, label in regex_to_labels if re.search(regex, title)]

if labels_to_add:
    issue.add_to_labels(*labels_to_add)
