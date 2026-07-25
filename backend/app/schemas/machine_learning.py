from pydantic import BaseModel, Field, field_validator


class MachineLearningFeaturesResponse(BaseModel):
    dataset_id: int
    rows: int
    numeric_features: list[str]
    recommended_features: list[str]
    max_rows: int


class MachineLearningRequest(BaseModel):
    features: list[str] | None = Field(default=None, max_length=50)
    contamination: float = Field(default=0.05, gt=0, le=0.5)
    lof_neighbors: int = Field(default=20, ge=2, le=200)

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [feature.strip() for feature in value if feature.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("特征字段不能重复")
        if not cleaned:
            raise ValueError("至少选择一个特征字段")
        return cleaned
