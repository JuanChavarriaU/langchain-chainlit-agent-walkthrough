import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI 

load_dotenv()

class llm_handler():  

    @staticmethod
    def get_llm() -> ChatOpenAI:
        """Returns a ChatOpenAI instance configured with environment variables."""
        return ChatOpenAI(
            model=os.getenv("MODEL"),
            api_key=os.getenv("GITHUB_TOKEN"),
            base_url=os.getenv("ENDPOINT"),
            streaming=True
        )   
    

