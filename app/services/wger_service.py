import httpx
from typing import Any, Dict, Optional

class WgerService:
    def __init__(self):
        self.base_url = "https://wger.de/api/v2"

    async def search_exercises(self, query: Optional[str] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        params = {
            "limit": limit,
            "offset": offset
        }
    
        if query:
            params["search"] = query

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/exerciseinfo/", params=params)
            response.raise_for_status()
            return response.json()
        
    async def get_exercise(self, exercise_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/exerciseinfo/{exercise_id}/")
            response.raise_for_status()
            return response.json()