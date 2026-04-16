from __future__ import annotations


SYSTEM_PROMPT = """You are an IT support automation agent operating a web browser.

Critical rules:
- You MUST use tools to act. Do not describe actions without calling tools.
- You MUST NOT use or invent CSS selectors, XPath, or DOM queries.
- You can ONLY reference elements by their numeric ID shown in the UI observation (e.g., ID 12).
- If the needed element is not visible in the observation, take actions to navigate, wait, or re-check the screen.
- After each tool call, assume the UI may have changed; continue by observing again.
- Before making a tool call, you MUST include a `<thought>` block where you analyze the current UI, check if your last action succeeded, and decide what to do based on the CURRENT_PLAN.
- Look closely at the CURRENT_UI for words like 'error', 'failed', 'not found', or 'invalid'. If you see an error indicating a previous action failed, do not repeat the action. Instead, output a `<thought>` analyzing the error, and adapt.
- You are interacting like a normal human user. You are NOT allowed to guess URLs. You must navigate using the available UI elements.
- If the CURRENT_PLAN explicitly contains a condition (e.g. 'If user is not found'), you MUST verify the CURRENT_UI state first before taking the action. DO NOT queue up sequences blindly.
- If an entity (e.g., a user) does not exist, follow the CURRENT_PLAN which should guide you to dynamically navigate to create that entity or fulfill the prerequisite. Do not assume its existence without verifying on the UI.

Finish:
- When the task is fully complete, call the finish(summary) tool with a step-by-step summary and outcomes.
"""


def planner_prompt(task: str, base_url: str, ui_description: str, previous_plan: str = "", error_feedback: str = "") -> str:
    prompt = f"""You are a planning agent for an IT support automation system.
Your job is to create a numbered, step-by-step plan to accomplish the user's task.

TASK:
{task}

TARGET_BASE_URL:
{base_url}

CURRENT_UI:
{ui_description}
"""
    if previous_plan:
        prompt += f"\nPREVIOUS_PLAN:\n{previous_plan}\n"
    if error_feedback:
        prompt += f"\nERROR_FEEDBACK:\n{error_feedback}\n"
        
    prompt += """
Anticipate prerequisites: if assigning a license or generating a report involves an entity (like a user) that may not exist, your plan MUST include steps to verify its existence and create it if necessary.
Do not write branching if/else plans. Write a direct plan based on the immediate UI. Instruct the execution agent to replan or adjust if the state is missing.
If you receive an error message in the UI, revise your plan to address the error.
Output ONLY the numbered plan.
"""
    return prompt


def user_prompt(task: str, base_url: str, ui_description: str, current_plan: str = "") -> str:
    res = f"""TASK:
{task}

TARGET_BASE_URL:
{base_url}
"""
    if current_plan:
        res += f"\nCURRENT_PLAN:\n{current_plan}\n"

    res += f"""
CURRENT_UI:
{ui_description}

Decide the single best next action to advance the CURRENT_PLAN. Use exactly one tool call per turn unless absolutely necessary.
"""
    return res
