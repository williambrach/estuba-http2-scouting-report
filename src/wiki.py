from collections import defaultdict
from typing import Union

import requests
from bs4 import BeautifulSoup

from constants import logger, n2id


def process_team_picks(picks: defaultdict, n2id: dict) -> list:
    processed_picks = []
    for role in picks:
        for name, pick in picks[role].items():
            processed_picks.append(
                {
                    "name": name,
                    "picks": pick,
                    "icon": f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{n2id[name]}.png",
                }
            )
    return processed_picks


def sort_dictionary(dictionary: dict) -> dict:
    return dict(sorted(dictionary.items(), key=lambda item: item[1], reverse=True))


def process_bans(bans: defaultdict, n2id: dict) -> list:
    processed_bans = []
    for name, count in bans.items():
        processed_bans.append(
            {
                "name": name,
                "count": count,
                "icon": f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{n2id[name]}.png",
            }
        )
    return processed_bans


def get_team_data_from_lol_wiki(team: str) -> Union[list, list, list]:
    # params
    # ----------------------
    query = """https://lol.fandom.com/wiki/Hitpoint_2nd_Division_Challengers/2023_Season/Summer_Season/Match_History"""
    team_picks = {
        "top": defaultdict(lambda: 0),
        "jungle": defaultdict(lambda: 0),
        "mid": defaultdict(lambda: 0),
        "adc": defaultdict(lambda: 0),
        "supp": defaultdict(lambda: 0),
    }
    bans = defaultdict(lambda: 0)
    bans_against = defaultdict(lambda: 0)
    data_found = False
    # ----------------------
    team_picks_processed = {
        "top": [],
        "jungle": [],
        "mid": [],
        "adc": [],
        "supp": [],
    }
    bans_processed = []
    bans_against_processed = []
    logger.info(f"Looking for team - {team}")
    logger.info(f"Query url - {query}")

    # process html
    # ----------------------
    try:
        response = requests.get(query)
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find_all(class_="wide-content-scroll")[0].find("table")
        table_data = []
        for row in table.find_all("tr"):
            row_data = []
            for cell in row.find_all("td"):
                row_data.append(cell)
            table_data.append(row_data)
    except Exception as e:
        logger.error(f"Error in parsing HTML - {str(e)}")
        return [], [], []

    # process html data
    # ----------------------
    for row_data in table_data:
        if row_data == []:
            continue
        data_found = True
        row = {
            "date": row_data[0].text,
            "blue": row_data[2].find("a")["title"],
            "red": row_data[3].find("a")["title"],
            "winner": row_data[4].find("a")["title"],
            "bans_red": [c["title"] for c in row_data[6].find_all("span")],
            "bans_blue": [c["title"] for c in row_data[5].find_all("span")],
            "picks_red": [c["title"] for c in row_data[8].find_all("span")],
            "picks_blue": [c["title"] for c in row_data[7].find_all("span")],
        }
        if team.lower() in row['blue'].lower() or team.lower() in row['red'].lower():
            side = "blue" if team.lower() in row["blue"].lower() else "red"
            opponent = "red" if side == "blue" else "blue"
            roles = list(team_picks.keys())

            for i, champ in enumerate(row[f"picks_{side}"]):
                team_picks[roles[i]][champ] += 1

            for champ in row[f"bans_{side}"]:
                bans[champ] += 1

            for champ in row[f"bans_{opponent}"]:
                bans_against[champ] += 1

    if not data_found:
        logger.error("No data found.")
        return [], [], []

    # sort dicts
    # ----------------------
    for role in roles:
        team_picks[role] = sort_dictionary(team_picks[role])

    bans = sort_dictionary(bans)
    bans_against = sort_dictionary(bans_against)

    # fix format
    # ----------------------
    team_picks_processed = process_team_picks(team_picks, n2id)
    team_picks_processed = sorted(team_picks_processed, key=lambda x: x['picks'], reverse=True)
    bans_processed = process_bans(bans, n2id)
    bans_against_processed = process_bans(bans_against, n2id)

    logger.info(f"{team} parsing successful")
    return team_picks_processed, bans_processed, bans_against_processed
