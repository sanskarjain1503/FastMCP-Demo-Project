import json
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

"""
math server is local server created by own.
expense server is remote server created by own.

"""

SERVER = {
    "math":{
        "transport":"stdio",
        "command":"path of the uv",
        "args":[
            "run",
            "fastmcp",
            "run",
            "path of the server file"
        ]
    },
    "expense":{
        "transport":"streamable_http",
        "url": "http://splendid-gold-dingo.fastmcp.app/mcp" # path of the mcp server API
    },
    "manim-server":{
        "command": "path of the python",
        "args": [
            "path of the manim local server file"
        ],
        "env": {
            "MANIM_EXECUTABLE": ""
        }
    }
}

async def main():
    
    client =MultiServerMCPClient(SERVER)
    tools = await client.get_tools()
    
    
    named_tools = {}
    for tool in tools:
        named_tools[tool.name] = tool
        
    print("Available tools:", named_tools.keys())
        
    llm = ChatOpenAI(model="gpt-5")
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = "what is the product of 12 and 15"
    response = await llm_with_tools.ainvoke(prompt)
    
    if not getattr(response, "tool_call",None):
        print("\nLLM Reply:", response.content)
        return
    
    tool_message = []
    for tc in response.tool_calls:
        
        selected_tool = response.tool_calls[0]["name"]
        selected_tool_args = response.tool_calls[0]["args"]
        selected_tool_id = response.tool_calls[0]["id"]
        
        print(f"\n-> Executing remote tool: {selected_tool}")
        print("  with args:",selected_tool_args)
        
        result = await named_tools[selected_tool].ainvoke(selected_tool_args)
        tool_message.append(ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result)))
    
    final_response = await llm_with_tools.ainvoke([prompt, response, tool_message])
    print(final_response.content)
    

if __name__ == "__main__":
	asyncio.run(main())