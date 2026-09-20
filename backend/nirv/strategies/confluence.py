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
    signals: list[tuple[str, str]] = []
    if sweep in {"sell_side", "buy_side"}:
        signals.append(("BUY" if sweep == "sell_side" else "SELL", f"{sweep}_sweep"))
    if mss in {"bullish", "bearish"}:
        signals.append(("BUY" if mss == "bullish" else "SELL", f"{mss}_mss"))
    if fvg in {"bullish", "bearish"}:
        signals.append(("BUY" if fvg == "bullish" else "SELL", f"{fvg}_fvg"))

    directions = {direction for direction, _ in signals}
    if len(directions) != 1:
        return ConfluenceDecision(None, [], 0)

    confluences = [name for _, name in signals]
    if volume_confirmed:
        confluences.append("volume_confirmation")
    return ConfluenceDecision(next(iter(directions)), confluences, len(confluences))
