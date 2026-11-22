
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "runtime_error",
    "syntax_error",
    "type_error",
    "dependency_error",
    "configuration_error",
    "network_error",
    "resource_error",
    "unknown",
]

Severity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class ClassificationRequest(BaseModel):
    error: str = Field(min_length=1, max_length=10000)


class ClassificationResponse(BaseModel):
    category: Category
    severity: Severity
    summary: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)


CLASSIFICATION_SCHEMA = (ClassificationResponse.model_json_schema())
