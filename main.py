from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2 import extras

from src import api, wiki
from src.wiki import ROLE_ICONS

try:
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(
        host="postgresql.r5.websupport.sk",
        database="brch_db",
        user="brch_admin",
        password="Ps8zV>95Dg",
        connect_timeout=600,
    )

    with conn.cursor() as cur:
        # Fetch teams data from the database
        cur.execute("SELECT id, name, queryname, url, stats FROM team")
        teams = cur.fetchall()
        teams = pd.DataFrame(teams, columns=["id", "name", "queryname", "url", "stats"])

        for _, team in teams.iterrows():
            # Handle team params
            # ----------------------------
            query = team["queryname"]
            team_id = team["id"]
            team_picks, bans, bans_against = wiki.get_team_data_from_lol_wiki(query)
            dt_string = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
            stats = {"picks": team_picks, "bans": bans, "bans_against": bans_against}
            stats = extras.Json(stats)

            # Update team stats
            # ----------------------------
            update_query = """
                UPDATE team
                SET stats = %s, last_update = %s
                WHERE id = %s
            """
            cur.execute(update_query, (stats, dt_string, team_id))

            cur.execute(
                f"SELECT id, name, lolprosurl, alternativeids, role FROM player WHERE teamid = {team_id}"
            )
            team_players = cur.fetchall()
            team_players = pd.DataFrame(
                team_players,
                columns=["id", "name", "lolprosurl", "alternativeids", "role"],
            )
            for _, player in team_players.iterrows():
                url = player["lolprosurl"]  # "https://lolpros.gg/player/goksi"
                player_id = player["id"]
                alts = (
                    [] if player["alternativeids"] is None else player["alternativeids"]
                )
                player_data = api.get_player_data_by_lolpros(url, last_n=20, alts=alts)
                player_data = extras.Json(player_data)
                update_player_query = """
                UPDATE player
                SET accounts = %s, last_update = %s, icon = %s
                WHERE id = %s
                """
                cur.execute(
                    update_player_query,
                    (player_data, dt_string, ROLE_ICONS[player["role"]], player_id),
                )

            # Commit the changes to the database
            conn.commit()

except Exception as e:
    print(e)
finally:
    # Close the cursor and the connection
    cur.close()
    conn.close()
