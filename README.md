# Agentic Trading

Based on the paper : https://arxiv.org/pdf/2412.20138

## Usage

Set the folowing env variables in a .env file
```
REDDIT_CLIENT_SECRET=""
REDDIT_CLIENT_ID=""
REDDIT_USER_AGENT=""
X_BEARER_TOKEN=""
GEMINI_API_KEY=""
```

## Features
- Multi agent collaborative framework.

## Methodology

### Sentiment Score calculation Algorithm
#### ChatGPT Sentiment Scores:
The paper details the process of obtaining sentiment scores using ChatGPT based on news headlines. The steps are as follows:
- Prompting ChatGPT: A specific prompt is used to instruct ChatGPT on how to evaluate news headlines. The prompt is:
- Headline Substitution: In the prompt, "company name" and "headline" are replaced with the actual company name and the respective news headline being evaluated.
- ChatGPT Evaluation: ChatGPT, acting as a financial expert, analyzes the provided news headline and gives a one-word answer ("YES", "NO", or "UNKNOWN") on the first line, followed by a concise explanation on the next. The prompt instructs ChatGPT to consider only the provided headline as the source of information. The temperature of the GPT models is set to 0 to ensure reproducibility.
- Numerical Conversion: The textual responses from ChatGPT are then converted into numerical scores, referred to as "GPT-4 scores":
    - "YES" is mapped to 1 (positive).
    - "UNKNOWN" is mapped to 0 (neutral).
    - "NO" is mapped to -1 (negative).

## Resources

- LLM Debate : https://arxiv.org/pdf/2305.14325
- MetaGPT : https://github.com/geekan/MetaGPT ([Paper](https://cnaiwiki.com/aiweb/file/EN_METAGPT.pdf))

