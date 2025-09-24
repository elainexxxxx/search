import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Setup vLLM LLM client
llm = ChatOpenAI(
    model="hosted_vllm/Qwen3-235B-A22B-GPTQ-Int4",
    openai_api_base="http://10.96.184.114:8001/vllm/v1",
    openai_api_key="dummy",  # Required by LangChain, but not used by vLLM
    temperature=0
)

# Define MCP servers
client = MultiServerMCPClient(
    {
        "search": {
            "url": "http://127.0.0.1:8000/mcp",
            "transport": "streamable_http"
        }
    }
)

async def main():
    # Fetch tools from the MCP server
    tools = await client.get_tools()

    # Create the ReAct Agent with your LLM and tools
    agent = create_react_agent(llm, tools)

    # Define the test input
    query = "Find similar translation pairs to: 'All employees must wear safety helmets in the factory.' " \
            "Target language is Chinese and return top 3 matches."

    # Send the query to the agent
    response = await agent.ainvoke({"messages": query})

    # Print the result
    print("\n🔍 Agent Response:")
    print(response)

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())

