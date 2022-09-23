import requests
from dotenv import dotenv_values
from rocketry import Rocketry

from internal.database import database
from internal.logic.results.get_points import get_points

config = dotenv_values(".env")

app = Rocketry(config={'task_execution': 'async'})


@app.task("every 60 seconds")
def update_users():
    ip = config["F1_API"]

    event_url = f"http://{ip}/event/next"
    event_res = requests.get(event_url)
    event = event_res.json()

    season = event["season"]

    calendar_url = f"http://{ip}/calendar/{season}"
    calendar_res = requests.get(calendar_url)
    calendar = calendar_res.json()

    for round in calendar["events"]:
        race = round["round"]

        bets = list(database["Bets"].find({"round": race}))

        race_url = f"http://{ip}/results/race/{season}/{race}"
        race_res = requests.get(race_url)
        results = race_res.json()

        if "results" in results.keys():
            for bet in bets:
                round_points = get_points(results["results"], bet)

                database["Bets"].update_one({"uuid": bet["uuid"], "round": race}, {"$set": {
                    "points": round_points
                }})

    users = list(database["Users"].find({}, {"_id": False}).sort("points", -1))

    for user in users:
        all_bets = list(database["Bets"].find({"uuid": user["uuid"], "season": season}))

        all_points = 0

        for bet in all_bets:
            all_points += bet["points"]

        database["Users"].update_one({"uuid": user["uuid"]}, {"$set": {
            "points": all_points
        }})
