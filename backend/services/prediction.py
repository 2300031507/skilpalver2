from backend.schemas.prediction import RiskPredictionRequest, RiskPredictionResponse, RiskScores
from backend.clients.ml_client import MlClient
import httpx


ml_client = MlClient(base_url="http://localhost:8001")
NOTIFICATIONS_BASE_URL = "http://localhost:8002"


async def request_risk_prediction(payload: RiskPredictionRequest, actor: dict) -> RiskPredictionResponse:
    raw = await ml_client.predict_risk(student_id=payload.student_id, course_id=payload.course_id)
    scores = RiskScores(
        academic_risk=raw["academic_risk"],
        dropout_probability=raw["dropout_probability"],
        recovery_probability=raw["recovery_probability"],
    )
    risk_level = max(scores.academic_risk, key=scores.academic_risk.get)
    try:
        async with httpx.AsyncClient(base_url=NOTIFICATIONS_BASE_URL) as client:
            await client.post(
                "/evaluate",
                json={
                    "student_id": payload.student_id,
                    "course_id": payload.course_id,
                    "risk_level": risk_level,
                    "academic_risk": scores.academic_risk,
                    "dropout_probability": scores.dropout_probability,
                    "recovery_probability": scores.recovery_probability,
                },
                timeout=2.0,
            )
    except Exception as e:
        print(f"Failed to send prediction to notification service: {e}")
    return RiskPredictionResponse(
        student_id=payload.student_id,
        course_id=payload.course_id,
        risk_level=risk_level,
        scores=scores,
    )
