import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.


def get_champ_name_to_id() -> dict:
    n2id = {}
    champs_assets = requests.get(
        "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/en_gb/v1/champion-summary.json"
    ).json()
    for c in champs_assets:
        n2id[c["name"]] = c["id"]

    new_n2id = {}
    for k in n2id:
        if "'" in k:
            new_k = k.replace("'", "")
            new_n2id[new_k] = n2id[k]
        if " " in k:
            new_k = k.replace(" ", "")
            new_n2id[new_k] = n2id[k]
    n2id.update(new_n2id)
    n2id = {key.lower(): value for key, value in n2id.items()}
    return n2id


def create_logger() -> logging.getLogger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


n2id = get_champ_name_to_id()
LOL_API_KEY = os.getenv("LOL_API_KEY")
logger = create_logger()
