import os

import requests
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.internal.auth import decode_user
from app.internal.database import database
from app.internal.models.betting.bet import BetExample, BaseBet, FullBet
from app.internal.models.betting.user import User
from app.internal.models.general.message import Message, create_message

router = APIRouter(
    tags=["Bet"],
)


@router.get("/bet/{season}/{race}",
            response_model=FullBet,
            responses={
                404: {"model": Message, "content": {
                    "application/json": {
                        "example": create_message("User not found"),
                    }
                }},
                200: {"model": FullBet, "content": {
                    "application/json": {
                        "example": BetExample
                    }
                }},
            })
def get_bet(season: int, race: int, auth_user: User = Depends(decode_user)):
    user = database["Users"].find_one({"username": auth_user.username, "uuid": auth_user.uuid})

    if not user:
        return JSONResponse(status_code=404, content=create_message("User not found"))

    bet = database["Bets"].find_one({"uuid": user["uuid"], "season": season, "round": race})

    if not bet:
        return JSONResponse(status_code=404, content=create_message("Bet not found"))

    return bet


@router.post("/bet",
             response_model=FullBet,
             responses={
                 404: {"model": Message, "content": {
                     "application/json": {
                         "example": create_message("User not found")
                     }
                 }},
                 409: {"model": Message, "content": {
                     "application/json": {
                         "example": create_message("Bet already exists")
                     }
                 }},
                 200: {"model": FullBet, "content": {
                     "application/json": {
                         "example": BetExample
                     }
                 }}
             })
def create_bet(bet: BaseBet, auth_user: User = Depends(decode_user)):
    ip = os.getenv("F1_API")

    url = f"http://{ip}/event/next"

    res = requests.get(url)
    data = res.json()

    bet.p1 = bet.p1.upper()
    bet.p2 = bet.p2.upper()
    bet.p3 = bet.p3.upper()

    if bet.p1 == bet.p2 or bet.p2 == bet.p3 or bet.p1 == bet.p3:
        return JSONResponse(status_code=409, content=create_message("Duplicate drivers"))

    bet = jsonable_encoder(bet)

    drivers_url = f"http://{ip}/drivers/{data['season']}"
    drivers_res = requests.get(drivers_url)
    drivers_data = drivers_res.json()
    drivers = drivers_data["drivers"]

    driver_codes = []

    for driver in drivers:
        driver_codes.append(driver["code"])

    if not bet["p1"] in driver_codes or not bet["p2"] in driver_codes or not bet["p3"] in driver_codes:
        return JSONResponse(status_code=404, content=create_message("Driver not found"))

    bet["season"] = data["season"]
    bet["round"] = data["round"]
    bet["points"] = 0
    bet["uuid"] = auth_user.uuid

    user = database["Users"].find_one({"username": auth_user.username, "uuid": auth_user.uuid})

    if not user:
        return JSONResponse(status_code=404, content=create_message("User not found"))

    if list(database["Bets"].find(
            {"uuid": user["uuid"], "season": bet["season"], "round": bet["round"]})):
        return JSONResponse(status_code=409, content=create_message("Bet already exists"))

    new_bet = database["Bets"].insert_one(bet)

    created_bet = database["Bets"].find_one({"_id": new_bet.inserted_id})

    return created_bet


@router.put("/bet",
            response_model=Message,
            responses={
                404: {"model": Message, "content": {
                    "application/json": {
                        "example": create_message("User not found"),
                    }
                }},
                200: {"model": Message, "content": {
                    "application/json": {
                        "example": create_message("Bet updated successfully")
                    }
                }},
            })
def edit_bet(p1: str, p2: str, p3: str, auth_user: User = Depends(decode_user)):
    user = database["Users"].find_one({"username": auth_user.username, "uuid": auth_user.uuid})

    if not user:
        return JSONResponse(status_code=404, content=create_message("User not found"))

    ip = os.getenv("F1_API")

    url = f"http://{ip}/event/next"

    res = requests.get(url)
    data = res.json()

    bet = database["Bets"].find_one({"uuid": user["uuid"], "season": data["season"], "round": data["round"]})

    if not bet:
        return JSONResponse(status_code=404, content=create_message("Bet not found"))

    ip = os.getenv("F1_API")

    drivers_url = f"http://{ip}/drivers/{data['season']}"
    drivers_res = requests.get(drivers_url)
    drivers_data = drivers_res.json()
    drivers = drivers_data["drivers"]

    driver_codes = []

    for driver in drivers:
        driver_codes.append(driver["code"])

    if not p1.upper() in driver_codes or not p2.upper() in driver_codes or not p3.upper() in driver_codes:
        return JSONResponse(status_code=404, content=create_message("Driver not found"))

    database["Bets"].update_one({"_id": bet["_id"]}, {"$set": {
        "p1": p1.upper(),
        "p2": p2.upper(),
        "p3": p3.upper()
    }})

    return create_message("Bet updated successfully")


@router.delete("/bet",
               response_model=Message,
               responses={
                   404: {"model": Message, "content": {
                       "application/json": {
                           "example": create_message("User not found")

                       }
                   }},
                   200: {"model": Message, "content": {
                       "application/json": {
                           "example": create_message("Bet deleted successfully")
                       }
                   }},
               })
def delete_bet(auth_user: User = Depends(decode_user)):
    user = database["Users"].find_one({"username": auth_user.username, "uuid": auth_user.uuid})

    if not user:
        return JSONResponse(status_code=404, content=create_message("User not found"))

    ip = os.getenv("F1_API")

    url = f"http://{ip}/event/next"

    res = requests.get(url)
    data = res.json()

    bet = database["Bets"].find_one({"uuid": user["uuid"], "season": data["season"], "round": data["round"]})

    if not bet:
        return JSONResponse(status_code=404, content=create_message("Bet not found"))

    database["Bets"].delete_one({"_id": bet["_id"]})

    return create_message("Bet deleted successfully")