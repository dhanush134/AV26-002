from pydantic import BaseModel, ConfigDict


MEDICAL_DISCLAIMER = (
    "This is a preventive wellness insight, not a medical diagnosis. "
    "Please consult a qualified healthcare professional for medical advice."
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
