# IT Support Agent

## Agent Core

This directory contains the core intelligence and browser automation loop for the IT Support Agent. The agent marries **LangGraph** (for graph-based state management and LLM reasoning) with **Playwright** (for headless browser automation) to autonomously perform administrative tasks in the IT support panel.

### File Structure

```text
agent_core/
├── __main__.py          # Python execution entry point, routes to runner
├── config.py            # Environment validation and settings
├── browser/             # Playwright browser interaction module
│   ├── observer.py      # Injects JS scripts into the DOM to extract a machine-readable UI tree
│   └── tools.py         # LLM action definitions (click, type_text, select_option, etc.)
├── engine/              # LangGraph orchestration engine
│   ├── graph.py         # Defines the state machine nodes and edges
│   ├── nodes.py         # The actual logic executed at each graph state (Observe, Reason, Tool)
│   ├── runner.py        # Initializes the browser and executes the async interaction loop
│   └── state.py         # `TypedDict` definition for tracking tasks, steps, and history
├── models/              # Pydantic LLM models and core prompts
│   └── prompts.py       # ReAct and planner prompt definitions
└── utils/               # Shared utilities
    └── logger.py        # JSON-structured logging setup for observability
```

### Architecture

The agent is designed around a continuous **ReAct (Reasoning and Acting) loop** powered by a LangGraph state machine.

At a high level, the system separates:
1. **Perception**: Extracting human-readable labels and bounding boxes from the DOM.
2. **Cognition**: Using Gemini (or any structured output LLM) to draft an implementation plan and pick the correct next action to take.
3. **Execution**: Mapping the LLM's selected logical tool (e.g. `click(element_id=3)`) strictly to Playwright automation commands in the active browser context.

### State Machine Flow

The execution cycle generally follows this recurring loop:

1. **Initialization (`runner.py`)**: A task is passed to the runner. The runner launches Playwright, configures the base context, navigates to the target URL, and injects the initial state into the graph.
2. **Node 1: Observation (`observe_ui`)**: The agent reads the current DOM, filtering out invisible/disabled elements, and compiles a simplified UI layout of interactable elements containing an integer `[ID]`.
3. **Node 2: Planning (`planner_node`)**: The LLM reviews the task against the current UI and generates/revises a step-by-step action plan.
4. **Node 3: Reasoning (`reasoning_node`)**: The agent evaluates the current plan against the immediate UI and selects exactly one tool call to execute (e.g., clicking a specific element ID).
5. **Node 4: Tool Execution (`tool_node`)**: The command is handed off to Playwright, which interacts with the browser page. Playwright awaits resolution / network stability.
6. **Cycle**: The agent repeats from Observation (Step 2) until the `finish` tool is called by the LLM, indicating task completion.

### How to Use

The agent core can be run interactively as a CLI, or embedded within a larger service (such as a Telegram Bot).

#### Embedded Execution
You can import and trigger the async generator from other Python modules:
```python
import asyncio
from agent_core.engine.runner import run_task

async def my_script():
    # Pass headed=True to watch the browser work
    result = await run_task("Assign Alice a GitHub Enterprise License", url="http://localhost:8000/", headed=False, max_steps=40)
    print(result)

asyncio.run(my_script())
```

#### Interactive CLI
Change into the root directory of the repository and launch the interactive agent CLI:
```bash
python -m agent_core --url http://localhost:8000/ --headed
```
You can then sequentially pass it natural language prompts to perform. To exit, type `/exit`.
