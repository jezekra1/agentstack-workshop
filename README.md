# Agent Stack workshop

![agent-stack-light](assets/agent-stack-light.svg#gh-light-mode-only)
![agent-stack-dark](assets/agent-stack-dark.svg#gh-dark-mode-only)


This workshop will guide you through building a simple agent for searching flights
with MCP tool integration.

The workshop is organized into small sections or steps, iteratively leveraging more
features from the Agent Stack:

| Step                                                        | Description                                                                                                                                |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **[01-clone-template](./steps/01-clone-template.md)**       | Clone agent starter template and try the example agent                                                                                     |
| **[02-create-mcp-agent](./steps/02-create-mcp-agent.md)**   | Create a basic AI agent searching  with [Kiwi.com MCP server](https://mcp-install-instructions.alpic.cloud/servers/kiwi-com-flight-search) |
| **[03-add-form](./steps/03-add-form.md)**                   | Use LLM to generate interactive form for flight details                                                                                    |
| **[04-visualize-results](./steps/04-visualize-results.md)** | Create interactive HTML and static PNG map of the routes from results                                                                      |
| **[05-add-settings](./steps/05-add-settings.md)**          | Allow users to turn off PNG or HTML output                                                                                                 |
| **[06-save-conversation](./steps/06-save-conversation.md)** | Store conversation using the Platform Context Store                                                                                        |
| **[07-observability](./steps/07-observability.md)**         | Use [Arize Phoenix](https://phoenix.arize.com/) to visualize and debug agent thinking                                                      |
