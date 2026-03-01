import httpx


class MlClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def predict_risk(self, student_id: str, course_id: str):
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                response = await client.post(
                    "/predict",
                    json={"student_id": student_id, "course_id": course_id},
                    timeout=2.0,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"ML service unreachable: {e}")
            # Return fallback data
            return {
                "academic_risk": {"low": 0.5, "medium": 0.3, "high": 0.2},
                "dropout_probability": 0.1,
                "recovery_probability": 0.8
            }

