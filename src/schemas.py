from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class ToolSchema:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class BedrockToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]

    def to_bedrock_format(self) -> dict[str, Any]:
        return {
            "toolSpec": {
                "name": self.name,
                "description": self.description,
                "inputSchema": {"json": self.input_schema},
            }
        }


class BedrockMessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class BedrockMessage:
    role: BedrockMessageRole
    content: list[dict[str, Any]]


@dataclass
class ToolUseRequest:
    tool_id: str
    tool_name: str
    tool_input: dict[str, Any]
