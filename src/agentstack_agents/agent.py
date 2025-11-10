import base64
import os
from typing import Annotated, AsyncGenerator

from agentstack_sdk.server.store.platform_context_store import PlatformContextStore
from openinference.instrumentation.beeai import BeeAIInstrumentor

from agentstack_agents.visualize import create_interactive_map, create_static_map
from a2a.types import (
    FilePart,
    FileWithBytes,
    Message,
    TextPart,
)
from agentstack_sdk.a2a.extensions import (
    FormExtensionServer,
    FormRender,
    FormResponse,
    LLMServiceExtensionSpec,
    LLMServiceExtensionServer,
    FormExtensionSpec,
    SettingsExtensionServer,
    SettingsExtensionSpec,
    SettingsRender,
    CheckboxGroupField,
    CheckboxField,
    CitationExtensionServer,
    CitationExtensionSpec,
    Citation,
    PlatformApiExtensionServer,
    PlatformApiExtensionSpec,
)
from agentstack_sdk.a2a.types import AgentMessage, RunYield, RunYieldResume
from agentstack_sdk.platform import File
from agentstack_sdk.server import Server
from agentstack_sdk.server.context import RunContext
from beeai_framework.adapters.agentstack.backend.chat import AgentStackChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.events import RequirementAgentFinalAnswerEvent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModelParameters
from beeai_framework.tools import tool
from beeai_framework.tools.mcp import MCPTool
from mcp.client.streamable_http import streamablehttp_client

from agentstack_agents.visualize import prepare_flight_data

server = Server()

BeeAIInstrumentor().instrument()


@server.agent()
async def flight_search_agent(
    input: Message,
    llm_ext: Annotated[
        LLMServiceExtensionServer,
        LLMServiceExtensionSpec.single_demand(suggested=("openai:gpt-4o",)),
    ],
    form_extension: Annotated[FormExtensionServer, FormExtensionSpec(None)],
    settings: Annotated[
        SettingsExtensionServer,
        SettingsExtensionSpec(
            params=SettingsRender(
                fields=[
                    CheckboxGroupField(
                        id="create_visualization",
                        fields=[
                            CheckboxField(id="png", label="Create PNG Visualization", default_value=True),
                            CheckboxField(id="html", label="Create HTML Visualization", default_value=True),
                        ],
                    ),
                ],
            ),
        ),
    ],
    citation: Annotated[CitationExtensionServer, CitationExtensionSpec()],
    _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
    context: RunContext,
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Search and visualize flights"""
    await context.store(input)

    llm = AgentStackChatModel(parameters=ChatModelParameters(stream=True))
    llm.set_context(llm_ext)

    client = streamablehttp_client("https://mcp.kiwi.com")
    kiwi_tools = await MCPTool.from_client(client)

    prompt = f"Search flights for the user query: {input.parts[0].root.text}"

    create_visualization_settings = settings.parse_settings_response().values["create_visualization"].values
    create_png = create_visualization_settings["png"].value
    create_html = create_visualization_settings["html"].value
    create_visualization = create_png or create_html
    static_png_bytes = None
    interactive_html_bytes = None

    @tool
    async def ensure_all_data(form: FormRender) -> FormResponse | None:
        """
        Tool that ensures that all the required data is provided (flight dates, destination, origin, etc.).

        Args:
            form: A form that asks user for the missing inputs that are required
        Returns:
            All missing fields in a dictionary: {"start_date": ...}
        """
        return await form_extension.request_form(form=FormRender.model_validate(form))

    @tool
    async def visualize_flights(flights: list[list[str]]) -> None:
        """
        Tool that visualizes flights and saves them to a file. Use to visualize all flights from search results.
        Args:
            flights: A list of flights with waypoints (list of airport codes), for example,
                [
                    ["PRG", "LAS"],  # Direct flight
                    ["JFK", "LHR", "DXB", "SIN"],  # Flight with 2 layovers
                    # Add more flights here
                ]
        """
        nonlocal static_png_bytes, interactive_html_bytes
        # Define your flights with waypoints (list of airport codes)
        flights_gdf, airports_gdf = prepare_flight_data(flights)
        if create_png:
            static_png_bytes = create_static_map(flights_gdf, airports_gdf)
        if create_html:
            interactive_html_bytes = create_interactive_map(flights_gdf, airports_gdf)

    final_answer = []
    async for event, meta in RequirementAgent(
        llm=llm,
        tools=[*kiwi_tools, ensure_all_data, visualize_flights],
        requirements=[
            ConditionalRequirement(ensure_all_data, force_at_step=1),
            ConditionalRequirement(visualize_flights, force_after=kiwi_tools, enabled=create_visualization),
        ],
    ).run(prompt):
        match event:
            case RequirementAgentFinalAnswerEvent(delta=delta):
                final_answer.append(delta)
                yield delta

    final_message = AgentMessage(parts=[TextPart(text="".join(final_answer))])

    if static_png_bytes is not None:
        base64_string = base64.b64encode(static_png_bytes).decode("utf-8")
        file_part = FilePart(file=FileWithBytes(bytes=base64_string, mime_type="image/png", name="flights.png"))
        final_message.parts.append(file_part)
        yield file_part

    if interactive_html_bytes is not None:
        file = await File.create(filename="flights.html", content=interactive_html_bytes, content_type="text/html")
        final_message.parts.append(file.to_file_part())
        yield file.to_file_part()

    yield citation.message(citations=[Citation(url="https://kiwi.com", title="Kiwi.com, search engine for flights")])
    await context.store(final_message)


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        context_store=PlatformContextStore(),
        configure_telemetry=True,
    )


if __name__ == "__main__":
    run()
