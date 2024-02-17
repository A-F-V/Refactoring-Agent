from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI


def test_agent(input: str):
    tools = []
    # Get the prompt to use - you can modify this!
    prompt = hub.pull("hwchase17/openai-functions-agent")
    # Choose the LLM that will drive the agent
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    # Construct the OpenAI Functions agent
    agent_runnable = create_openai_functions_agent(llm, tools, prompt)

    # Create the agent executor
    agent_executor = AgentExecutor(agent=agent_runnable, tools=tools)

    # Run the agent
    response: str = agent_executor.invoke({"input": input})
    return response
