from collections import defaultdict
from typing import Union

import requests
from bs4 import BeautifulSoup
from riotwatcher import ApiError, LolWatcher

from constants import LOL_API_KEY, logger, n2id


def get_champions_played(
    region: str, summoner_name: str, champions: defaultdict, last_n: int = 20
) -> defaultdict:
    try:
        watcher = LolWatcher(LOL_API_KEY,timeout=600)
        summoner = watcher.summoner.by_name(region, summoner_name)
        match_history = watcher.match.matchlist_by_puuid(region, summoner["puuid"])
        last_20_matches = match_history[:last_n]
        for match in last_20_matches:
            match_data = watcher.match.by_id(match_id=match, region=region)
            for player in dict(match_data)["info"]["participants"]:
                if player["puuid"] == summoner["puuid"]:
                    champ_name = player["championName"]
                    win = 1 if player["win"] else 0
                    stat = champions[champ_name]
                    stat = (stat[0] + 1, stat[1] + win)
                    champions[champ_name] = stat
        return champions
    except ApiError as err:
        logger.error(f"Error while retrieving summoner information: {err}")
        return None, []


def get_rank_by_queue(region: str, summoner_name: str, queue: str) -> str:
    try:
        watcher = LolWatcher(LOL_API_KEY)
        summoner = watcher.summoner.by_name(region, summoner_name)
        ranked_data = watcher.league.by_summoner(region, summoner["id"])
        for queue_data in ranked_data:
            if queue_data["queueType"] == queue:
                rank = (
                    queue_data["tier"]
                    + " "
                    + queue_data["rank"]
                    + " "
                    + str(queue_data["leaguePoints"])
                )
                break
        else:
            rank = "Unranked"
        return rank
    except ApiError as err:
        logger.error(f"Error while retrieving summoner information: {err}")
        return "Unranked"


def get_ranked_stats(
    summoner_name: str, region: str = "euw1", last_n: int = 20
) -> Union[str, str, defaultdict]:
    champions = defaultdict(lambda: (0, 0))
    soloq_rank = get_rank_by_queue(region, summoner_name, "RANKED_SOLO_5x5")
    flex_rank = get_rank_by_queue(region, summoner_name, "RANKED_FLEX_SR")
    champions = get_champions_played(region, summoner_name, champions, last_n=last_n)

    logger.info(f"{summoner_name} | soloq : {soloq_rank} | flexq : {flex_rank}")
    return soloq_rank, flex_rank, champions


def calculate_win_rate(value: tuple) -> float:
    total_games, wins = value
    return round(wins / total_games * 100, 2) if total_games != 0 else 0


def get_player_data_by_lolpros(url: str, last_n: int = 20) -> object:
    player_name = url.split("/")[-1]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    # check if user has more acc
    account_elements = soup.find_all(class_="account")
    account_ids = [element.text.strip() for element in account_elements]

    # check if user has single acc 
    if len(account_ids) == 0:
        account_elements = soup.find_all(class_="--opgg")
        account_ids = [element['href'].split("=")[-1] for element in account_elements[:1]]
    player_data = {"accounts": [], "history": []}
    player_champs = defaultdict(lambda: (0, 0))
    logger.info(f"player - {player_name} | ids found - {account_ids}")
    for account_id in account_ids:
        opgg = f"https://www.op.gg/summoners/euw/{account_id}"
        soloq_rank, flex_rank, champions = get_ranked_stats(
            summoner_name=account_id, last_n=last_n
        )
        player_data["accounts"].append(
            {
                "account_name": account_id,
                "opgg": opgg,
                "soloq": soloq_rank,
                "flexq": flex_rank,
            }
        )
        for champ, value in champions.items():
            player_champs[champ] = (value[0], calculate_win_rate(value))

    player_champs = dict(
        sorted(player_champs.items(), key=lambda item: item[1], reverse=True)
    )
    for champ, stats in player_champs.items():
        player_data["history"].append(
            {
                "champion": champ,
                "played": stats[0],
                "win_rate": stats[1],
                "icon": f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{n2id.get(champ,-1)}.png",
            }
        )
    return player_data
