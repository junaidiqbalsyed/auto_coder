import warnings
warnings.filterwarnings('ignore')
import abc
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate,


class BaseAgent:
    def __init__(self, llm) -> None:
        self.llm = llm

    @abc.abstractmethod
    def parse_output(self, raw_result, parsed_output):
        raise NotImplementedError()

    def execute_task(self, **kwargs):
        
        # convert this to a system message 
        template = SystemMessagePromptTemplate.from_template(self.prompt_template)

        chat_prompt = ChatPromptTemplate.from_messages( [template] )

        # provide the input i.e., task 
        prompt = chat_prompt.format_prompt( **kwargs ).to_messages()

        # get the raw data from the llm
        raw_result = self.llm(prompt, stop=[self.stop_string])

        # parse the llm output 
        parsed_result = self.parse_output(raw_result.content)
        
        return parsed_result
