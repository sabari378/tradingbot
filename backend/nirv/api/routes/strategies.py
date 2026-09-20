from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StrictBool

from nirv.core.security import require_api_key
from nirv.services.strategy_controls import set_strategy_enabled
from nirv.services.strategy_dashboard import strategy_dashboard

router = APIRouter(tags=['strategies'])


class StrategyControl(BaseModel):
    enabled: StrictBool


@router.get('/strategies')
def list_strategies():
    return strategy_dashboard()


@router.post('/strategies/{strategy}/enabled', dependencies=[Depends(require_api_key)])
def toggle_strategy(strategy: str, body: StrategyControl):
    try:
        states = set_strategy_enabled(strategy, body.enabled)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {'strategy': strategy, 'enabled': states[strategy]}
