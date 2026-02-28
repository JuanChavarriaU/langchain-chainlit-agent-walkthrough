# create app.py with just the basics - an app that echoes back what i type. 
import chainlit as cl
from ai_interface.messages_interface import conversational_agent

def main():
    agent = conversational_agent()
    agent.start()
    agent.messages()

if __name__ == "__main__":
    main()