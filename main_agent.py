import vertexai
from google.adk.agents import LlmAgent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from contact_authorities_tool import ContactAuthoritiesTool
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.genai.types import Content, Part
import os
from dotenv import load_dotenv

# Load environment variables from .env file in the current directory
load_dotenv('.env')

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

# Initialize Vertex AI with environment variables
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION")
)
client = vertexai.Client(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION")
)

# Create an agent engine (experimental)
agent_engine = client.agent_engines.create()

agent = LlmAgent(
    model="gemini-2.0-flash",
    name="main_security_agent",
    instruction="""
You are a security orchestration agent. Your objective is to monitor security issues, take appropriate actions, and keep track of the situation using your memory. You should:

- Continuously assess how serious the issue is based on detailed descriptions from the VLM tool.
- Do not respond to every frame; instead, keep the details in memory.
- When you determine an action is required, ask the human operator for permission with a clear message.
- Use the token "ask_human:" at the start of your message when requesting human permission.
- If the human approves, trigger the appropriate tool to handle the action.
- Keep a memory of all events and actions taken to maintain full context.
- If the human has recently approved an action and it has been taken, do not ask for permission again for the same action.
- Instead, inform the human about the current status of the issue and ongoing actions without repeating the VLM description.
- Use the 'contact_authorities' tool to alert authorities when the issue is serious.
- Confirm to the human when an alert has been sent.

Always communicate clearly and keep the human informed about the situation and your actions.
""",
    tools=[PreloadMemoryTool(), ContactAuthoritiesTool()]
)

runner = Runner(
    agent=agent,
    app_name="security_app",
    session_service=VertexAiSessionService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        agent_engine_id=agent_engine.api_resource.name.split("/")[-1]
    ),
    memory_service=VertexAiMemoryBankService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        agent_engine_id=agent_engine.api_resource.name.split("/")[-1]
    )
)

import asyncio

async def send_to_main_agent(payload, user_id="user1", session_id=None):
    if session_id is None:
        session = await runner.session_service.create_session(app_name="security_app", user_id=user_id)
        session_id = session.id
    content = Content(role="user", parts=[Part(text=payload)])
    events = []
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        events.append(event)
    return [e.content.parts[0].text for e in events if e.content and e.content.parts], session_id
