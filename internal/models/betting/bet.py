from pydantic import BaseModel


class BaseBet(BaseModel):
    username: str
    p1: str
    p2: str
    p3: str


class FullBet(BaseBet):
    season: int
    round: int
    points: int


class BetResults(BaseModel):
    results: list[FullBet]


BetExample = {
    "username": "niek",
    "p1": "RUS",
    "p2": "LEC",
    "p3": "RUS",
    "season": 2022,
    "round": 16,
    "points": 2
}