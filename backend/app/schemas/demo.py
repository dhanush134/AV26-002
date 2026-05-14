from uuid import UUID

from pydantic import BaseModel


class FullDemoResponse(BaseModel):
    message: str
    user_id: UUID
    demo_scenario: str
    next_steps: dict[str, str]
