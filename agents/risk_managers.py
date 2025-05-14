from agents.utils.prompts import aggressive_prompt, neutral_prompt, conservative_prompt
from agents.utils.debate_utils import DebateEngine
from agents.utils.helpers import load_file

class RiskTeam:
    def __init__(self):
        self.engine = DebateEngine()


    def get_report(self, file_path):
        report = load_file(file_path=file_path)
        return report

    def generate_agent_context(self, report_path, share_name):

        report_content = self.get_report(file_path=report_path)

        # Defining agents
        agent_contexts = []
        agent_contexts.append([{"role": "user", "content": aggressive_prompt.format(share_name=share_name, report_content=report_content)}])
        agent_contexts.append([{"role": "user", "content": neutral_prompt.format(share_name=share_name, report_content=report_content)}])
        agent_contexts.append([{"role": "user", "content": conservative_prompt.format(share_name=share_name, report_content=report_content)}])

        agent_desc = ["Aggressive", "Neutral", "Conservative"]

        return agent_contexts, agent_desc
    
    def debate(self, report_path, report_category):
        agent_contexts, agent_desc = self.generate_agent_context(report_path) 
        self.engine.execute_rounds(
            agent_contexts=agent_contexts,
            agent_desc=agent_desc,
            num_rounds=2,
            report_category=report_category,
            debate_path = '/home/avishkar/Desktop/agentic_trading/tests/tcs-risk-debate.json'
        )


