from dataclasses import dataclass


@dataclass(frozen=True)
class ConfluenceDecision:
    direction: str | None
    confluences: list[str]
    score: int


def evaluate_confluence(
    *, sweep: str | None, mss: str | None, fvg: str | None, volume_confirmed: bool, news_blocked: bool
) -> ConfluenceDecision:
    if news_blocked:
        return ConfluenceDecision(None, ["news_blackout"], 0)
    direction = (
        "BUY"
        if sweep == "sell_side" and mss == "bullish" and fvg == "bullish"
        else "SELL"
        if sweep == "buy_side" and mss == "bearish" and fvg == "bearish"
        else None
    )
    confluences = []
    if direction:
        confluences = [f"{sweep}_sweep", f"{mss}_mss", f"{fvg}_fvg"] + (
            ["volume_confirmation"] if volume_confirmed else []
        )
    return ConfluenceDecision(direction, confluences, len(confluences))
