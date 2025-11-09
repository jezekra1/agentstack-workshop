# Get started with Agent Stack

## Step 1: install the Agent Stack

On MacOS and Linux you can install the Agent Stack cli by running the following script in the terminal:

```bash
sh -c "$(curl -LsSf https://raw.githubusercontent.com/i-am-bee/agentstack/HEAD/install.sh)"
```

for Windows follow [full installation instructions](https://agentstack.beeai.dev/introduction/quickstart)

For this workshop, we will use OpenAI models, select the OpenAI LLM provider and configure your API key when requested
during setup.

After a successful installation and setup, the command `agentstack list` should show the builtin example
agents:

```bash
$ agentstack list
SHORT ID  NAME                    STATE     DESCRIPTION      INTERACTION  LOCATION                                               MISSING ENV  LAST ERROR
3b906a27  Chat                    missing   Agent with mem…  multi-turn   agents/chat:0.4.1-rc2                                  <none>       <none>
6b27a943  RAG                     missing   RAG agent that…  multi-turn   agents/rag:0.4.1-rc2                                   <none>       <none>
1af40f1e  Single-turn Form Agent  missing   Example demons…  multi-turn   agents/form:0.4.1-rc2                                  <none>       <none>
```

## Step 2: clone the Agent starter template

The simplest way to create a new agent is to use
the [Agent Stack starter template](https://github.com/i-am-bee/agentstack-starter).

After you create a new repository on GitHub, clone using `git clone` and start the agent using `uv run server`.
See the README.md for repository structure and more details.

The agent should now show up in `agentstack list` as `example_agent` and also in `agenstack ui`. You can try sending
a message using `agentstack run <your-name>`, you should get a polite greeting.

![example-agent](../assets/01-example-agent.png)

Now we are ready to modify the agent with our code, see the next
part: **[02-create-mcp-agent](./02-create-mcp-agent.md)**.



