from openai import OpenAI

from agents.utils.llm_utils import GeminiFlash
from agents.utils.helpers import Color, load_file, write_json
from agents.db.db import DB, ResearchTeamDebate

from datetime import datetime
from pprint import pprint
import time
import os

class DebateEngine(object):
    """docstring for DebateEngine."""
    def __init__(self, DB_PATH):
        super(DebateEngine, self).__init__()

        self.llm = GeminiFlash()
        self.db = DB(DB_PATH) 

    def construct_message(
            self, 
            agents, 
            idx
            ):
        if len(agents) == 0:
            return {"role": "user", "content": "Can you double check that your answer is correct. Put your final answer in the form (X) at the end of your response."}

        prefix_string = "These are the arguments & opinions from other agents: "

        for agent in agents:
            agent_response = agent[idx]["content"]
            response = f"\n\n One agent's argument: ```{agent_response}```"

            prefix_string = prefix_string + response

        prefix_string = prefix_string + """\n\n Using the reasoning from other agents as additional advice, can you give an updated response - keeping in min the original task and guidelines you were provided with? Examine your arguments and that of other agents step by step. Put your answer in the form (X) at the end of your response."""
        return {"role": "user", "content": prefix_string}

    def generate_answer(self, answer_context):
        try:
            # response = self.llm.client.chat.completions.create(
            #     model=self.llm.model,
            #     messages=answer_context
            #     )
            response = self.llm.call(prompt = answer_context)
        except Exception as e:
            print("retrying due to an error......")
            print(e)
            time.sleep(20)
            return self.generate_answer(answer_context)

        return response

    def construct_assistant_message(self, response):
        # content = completion["choices"][0]["message"]["content"]
        # content = completion
        # content = completion.choices[0].message.content
        return {"role": "assistant", "content": response}
    
    def agent_context_to_str(self, agent_context):
        agent_context_str = ""

        for x in agent_context:
            item = f"""Role : {x['role']}
Content : {x['content']}
"""
            agent_context_str += item

        return agent_context_str

    def execute_rounds(
            self,
            date,
            ticker,
            agent_contexts,
            agent_desc,
            num_rounds=2,
            ):
        print(f"{Color.BLUE}Model : [{self.llm.model}]{Color.RESET}")
        response_dict = {}
        for round in range(num_rounds):
            for i, agent_context in enumerate(agent_contexts):

                if round != 0:
                    agent_contexts_other = agent_contexts[:i] + agent_contexts[i+1:]
                    message = self.construct_message(
                        agent_contexts_other, 
                        idx= 2 * round - 1
                        )
                    agent_context.append(message)

                agent_context_str = self.agent_context_to_str(agent_context)
                response = self.generate_answer(agent_context_str)
                # completion = "Sample completion"

                assistant_message = self.construct_assistant_message(response)
                agent_context.append(assistant_message)

                print(f"{Color.CYAN}-------------------------------------------------------------{Color.RESET}")
                print(f"{Color.BLUE}Agent : {agent_desc[i]}{Color.RESET}")
                print(f"{Color.GREEN}Response :- \n{Color.RESET}")
                print(f"{Color.GREEN}{response}\n{Color.RESET}")
                print(f"{Color.CYAN}-------------------------------------------------------------{Color.RESET}")

                # print(completion)

            time.sleep(3)
            
        bullish_argument_ = [ x['content'] for x in agent_contexts[0] if x['role']=='assistant' ]
        bearish_argument_ = [ x['content'] for x in agent_contexts[1] if x['role']=='assistant' ]

        bullish_argument = '\n'.join(bullish_argument_)
        bearish_argument = '\n'.join(bearish_argument_)

        debate_record = ResearchTeamDebate(
            date= datetime.strptime(date, "%Y-%m-%d"),
            ticker=ticker,
            bullish=bullish_argument,
            bearish=bearish_argument
        )

        self.db.create(debate_record)
        print(f"{Color.YELLOW}Saving debate for date : {date}{Color.RESET}")

        # response_dict[report_category] = agent_contexts
        # write_json(data = response_dict, file_path=debate_path)



if __name__ == "__main__":


    """
    Our purpose is to generate Bearish and Bullish perspective reports
    
    INPUT
        - Analysts Reports
        - 4 reports to be exact
        

    """

    engine = DebateEngine()

    pass