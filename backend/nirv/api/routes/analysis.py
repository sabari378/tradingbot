from fastapi import APIRouter

from nirv.agents.master import NirvMasterAgent
from nirv.schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    result = await NirvMasterAgent().analyze(request.model_dump())
    return AnalysisResponse(**result)
