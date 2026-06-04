import json
import re
import subprocess
import urllib.request
from datetime import date, datetime
from typing import List, Optional

from .models import ContributionData, ContributionDay, ContributionLevel, ContributionWeek
from .config import get_token, get_username_override


GRAPHQL_QUERY = (
    'query($username:String!)'
    '{user(login:$username)'
    '{contributionsCollection'
    '{contributionCalendar'
    '{totalContributions weeks'
    '{contributionDays'
    '{contributionCount date contributionLevel}}}}}}'
)

_USERNAME_RE = re.compile(r'^[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?$')


class GitHubServiceError(Exception):
    pass


def _run_gh(args: str, timeout: int = 30) -> tuple[bool, str]:
    import shlex
    try:
        result = subprocess.run(
            ["gh"] + shlex.split(args),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr or result.stdout
    except FileNotFoundError:
        raise GitHubServiceError(
            "GitHub CLI (gh) not found. Install it or set a token in ~/.config/github-grid/config.json"
        )
    except subprocess.TimeoutExpired:
        raise GitHubServiceError("GitHub CLI request timed out.")


def _graphql_direct(username: str) -> str:
    token = get_token()
    if not token:
        raise GitHubServiceError(
            "No GitHub token found. Set GITHUB_GRID_TOKEN env var or add 'token' to ~/.config/github-grid/config.json"
        )

    payload = json.dumps({
        "query": GRAPHQL_QUERY,
        "variables": {"username": username},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHubGrid/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise GitHubServiceError(f"GitHub API error {e.code}: {body}")
    except Exception as e:
        raise GitHubServiceError(f"GitHub API request failed: {e}")


def _get_username_direct() -> str:
    token = get_token()
    if not token:
        raise GitHubServiceError(
            "No GitHub token found. Set GITHUB_GRID_TOKEN env var or add 'token' to ~/.config/github-grid/config.json"
        )

    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "GitHubGrid/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["login"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise GitHubServiceError(f"GitHub API error {e.code}: {body}")
    except Exception as e:
        raise GitHubServiceError(f"GitHub API request failed: {e}")


def get_username() -> str:
    override = get_username_override()
    if override:
        return override

    token = get_token()
    if token:
        username = _get_username_direct()
        if _USERNAME_RE.match(username):
            return username
        raise GitHubServiceError("Invalid GitHub username format received.")

    success, output = _run_gh("api user --jq .login")
    if not success:
        raise GitHubServiceError("Failed to get GitHub username. Ensure 'gh auth login' has been run.")

    username = output.strip()
    if not _USERNAME_RE.match(username):
        raise GitHubServiceError("Invalid GitHub username format received.")

    return username


def _parse_level(level_str: str) -> ContributionLevel:
    mapping = {
        "NONE": ContributionLevel.NONE,
        "FIRST_QUARTILE": ContributionLevel.FIRST_QUARTILE,
        "SECOND_QUARTILE": ContributionLevel.SECOND_QUARTILE,
        "THIRD_QUARTILE": ContributionLevel.THIRD_QUARTILE,
        "FOURTH_QUARTILE": ContributionLevel.FOURTH_QUARTILE,
    }
    return mapping.get(level_str, ContributionLevel.NONE)


def _parse_response(json_text: str) -> ContributionData:
    data = json.loads(json_text)

    if "errors" in data:
        errors = data["errors"]
        msg = errors[0].get("message", "Unknown GraphQL error") if errors else "Unknown GraphQL error"
        raise GitHubServiceError(msg)

    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = calendar["totalContributions"]

    weeks: List[ContributionWeek] = []
    for week_data in calendar["weeks"]:
        days: List[ContributionDay] = []
        for day_data in week_data["contributionDays"]:
            d = date.fromisoformat(day_data["date"])
            count = day_data["contributionCount"]
            level = _parse_level(day_data["contributionLevel"])
            days.append(ContributionDay(d, count, level))
        weeks.append(ContributionWeek(days))

    return ContributionData(total, weeks, datetime.now())


def fetch_contributions(username: str) -> ContributionData:
    if not _USERNAME_RE.match(username):
        raise GitHubServiceError("Invalid GitHub username format.")

    token = get_token()
    if token:
        return _parse_response(_graphql_direct(username))

    args = f'api graphql -f query="{GRAPHQL_QUERY}" -F username="{username}"'
    success, output = _run_gh(args)
    if not success:
        raise GitHubServiceError("Failed to fetch contribution data from GitHub.")

    return _parse_response(output)
