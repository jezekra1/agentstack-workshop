# Make visualization outputs configurable

To showcase the settings extension of Agent Stack we can make the visualizations optional. Users can then turn
them off before sending a new request to the agent. The following example show the use of agent settings:

```python
from agentstack_sdk.a2a.extensions import (
    SettingsExtensionServer,
    SettingsExtensionSpec,
    SettingsRender,
    CheckboxGroupField,
    CheckboxField,
)

@server.agent()
async def flight_search_agent(
    ...,
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
):
    # define variables we will use to configure agent
    create_visualization_settings = settings.parse_settings_response().values["create_visualization"].values
    create_png = create_visualization_settings["png"].value
    create_html = create_visualization_settings["html"].value
    create_visualization = create_png or create_html

```

Now we can just add a few if statements and contitions:
```python
@server.agent()
async def flight_search_agent(...):
    @tool
    async def visualize_flights(flights: list[list[str]]) -> None:
        ...
        # save resource by skipping visualization if not required
        if create_png:
            static_png_bytes = create_static_map(flights_gdf, airports_gdf)
        if create_html:
            interactive_html_bytes = create_interactive_map(flights_gdf, airports_gdf)

    # updagte agent requirements:
    async for event, meta in RequirementAgent(
        llm=llm,
        tools=[*kiwi_tools, ensure_all_data, visualize_flights],
        requirements=[
            ...,
            ConditionalRequirement(visualize_flights, force_after=kiwi_tools, enabled=create_visualization),
        ],
    ).run(prompt):
        ...
```

Let's move on to the next topic: **[06-save-conversation](./06-save-conversation.md)**

