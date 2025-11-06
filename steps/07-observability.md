# Debug agent using the builtin observability

## Step 1: enable Arize Phoenix

To enable the builtin Arize Phoenix instance, run the `platform start` command with the extra option:

```bash
agentstack platform start --set phoenix.enabled=true
```

## Step 2: instrument agent

Install the required package to instrument BeeAI framework:

```bash
uv add openinference-instrumentation-beeai
```

Then add a few lines of code:

```python
from openinference.instrumentation.beeai import BeeAIInstrumentor

# Enable telemetry in the BeeAI framework
BeeAIInstrumentor().instrument()


@server.agent()
async def flight_search_agent(): ...


def run():
    server.run(
        ...,
        # Enable telemetry in the Agent Stack SDK
        configure_telemetry=True,
    )
```

Now open up your browser at `http://localhost:6006` and you should see traces for new messages
to the agent.

## Final step: profit

Congratulations! You've made it to the end of the workshop.

As a bonus, you can try adding the citation extension to show the users where the data come from, see
[citations documentation](https://agentstack.beeai.dev/build-agents/citations).