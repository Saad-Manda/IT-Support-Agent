# IT-Support-Agent

## Agent core (LangGraph + Playwright)

### Setup

- Install Python deps:

```bash
pip install -r requirements.txt
```

- Install Playwright browser:

```bash
playwright install chromium
```

### Run (against the `panel/` app)

1) Start the panel:

```bash
python -m panel.main
```

2) In another terminal, run the agent:

```bash
set GEMINI_API_KEY=YOUR_KEY
python -m agent_core "Navigate through the Panel and tell me exactly how many active users currently have an admin role." --url http://localhost:8000/ --headed
```
