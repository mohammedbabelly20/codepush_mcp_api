import boto3
from contextlib import AsyncExitStack

from mcp import ClientSession, stdio_client, StdioServerParameters

from .mcp_server import MCPServer
from .schemas import BedrockMessage, BedrockMessageRole, BedrockToolSpec, ToolUseRequest


class MCPClient:
    def __init__(self, codepush_access_key: str = None):
        self.codepush_access_key = codepush_access_key
        self.session: ClientSession | None = None
        self.tools = []
        self.messages = []
        self.bedrock_client = boto3.client(service_name="bedrock-runtime")
        self.exit_stack = AsyncExitStack()

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit_stack.__aexit__(exc_type, exc, tb)

    async def connect_to_server(self):
        mcp_server = MCPServer()
        connection_info = mcp_server.get_connection_info(self.codepush_access_key)
        server_params = StdioServerParameters(
            command=connection_info["command"],
            args=connection_info["args"],
            env=connection_info["env"],
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()
        self.tools = await self._get_available_tools()
        print(f"Connected to MCP server with tools: {self.tools}")

        return True

    async def process_query(self, query: str) -> list[BedrockMessage]:
        try:
            self._add_user_message(query)

            while True:
                response = self._call_llm()
                self._add_assistant_message(response)

                if response["stopReason"] != "tool_use":
                    break

                tool_results = await self._handle_tool_use(response)
                self._add_tool_results(tool_results)

            return self.messages

        except Exception as e:
            print(f"Error processing query: {e}")
            raise

    async def _get_available_tools(self):
        try:
            response = await self.session.list_tools()
            self.tools = [
                BedrockToolSpec(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                )
                for tool in response.tools
            ]

            return [tool.to_bedrock_format() for tool in self.tools]
        except Exception as e:
            print(f"Error getting MCP tools: {e}")
            raise

    def _add_user_message(self, text: str):
        self.messages.append(
            BedrockMessage(role=BedrockMessageRole.USER, content=[{"text": text}])
        )

    def _add_assistant_message(self, response: dict[str | None]):
        self.messages.append(
            BedrockMessage(
                role=BedrockMessageRole.ASSISTANT,
                content=response["output"]["message"]["content"],
            )
        )

    def _add_tool_results(self, tool_results: list[dict[str | None]]):
        self.messages.append(
            BedrockMessage(role=BedrockMessageRole.USER, content=tool_results)
        )

    async def _handle_tool_use(
        self, response: dict[str | None]
    ) -> list[dict[str | None]]:
        """Handle tool use requests from LLM response"""
        tool_requests = self._extract_tool_requests(response)
        tool_results = []

        for request in tool_requests:
            result = await self.session.call_tool(request.tool_name, request.tool_input)
            tool_results.append(self._format_tool_result(request.tool_id, result))

        return tool_results

    def _extract_tool_requests(
        self, response: dict[str | None]
    ) -> list[ToolUseRequest]:
        """Extract tool use requests from LLM response"""
        requests = []
        content = response["output"]["message"]["content"]

        for item in content:
            if "toolUse" in item:
                tool = item["toolUse"]
                requests.append(
                    ToolUseRequest(
                        tool_id=tool["toolUseId"],
                        tool_name=tool["name"],
                        tool_input=tool["input"],
                    )
                )

        return requests

    def _format_tool_result(self, tool_id: str, result) -> dict[str | None]:
        """Format tool result for conversation"""
        return {
            "toolResult": {
                "toolUseId": tool_id,
                "content": [{"text": result.content[0].text}],
            }
        }

    def _call_llm(self) -> dict[str | None]:
        """Call LLM with current conversation"""
        try:
            bedrock_messages = self._messages_to_bedrock_format()

            response = self.bedrock_client.converse(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                messages=bedrock_messages,
                toolConfig={"tools": self.tools},
                system=[
                    {"text": "Please keep your answers very short and to the point."}
                ],
            )
            return response

        except Exception as e:
            print(f"Error calling LLM: {e}")
            raise

    def _messages_to_bedrock_format(self) -> list[dict[str | None]]:
        """Convert internal messages to Bedrock format"""
        return [
            {"role": msg.role.value, "content": msg.content} for msg in self.messages
        ]

    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            print("Disconnected from MCP server")
        except RuntimeError as e:
            if "different task" in str(e) or "cancel scope" in str(e):
                print("Disconnected from MCP server (cross-task cleanup)")
            else:
                print(f"Error during cleanup: {e}")
                raise
        except Exception as e:
            print(f"Error during cleanup: {e}")
            raise
