# Prompts based on the ReAct framework

market_analyst_prompt = """You are a market analyst. Analyze the recent technical indicators for {share_name} stock and provide a structured report on market trends.  

Here is the extracted technical indicator data for AAPL over the period {start_date} to {end_date}

{technical_data}

### **Instructions**
1. **Momentum Indicators**: Analyze RSI and ADX to determine buying/selling pressure and trend strength.
2. **Volatility Indicators**: Evaluate Bollinger Bands and ATR to assess market stability.
3. **Volume Indicators**: Interpret VR values to understand trading activity.
4. **Trend & Price Action**: Identify patterns in MACD and CCI to predict potential reversals.
5. **Summary & Recommendations**: Provide a concluding analysis on the stock's movement, possible trend reversals, and trading insights.

Ensure the report is:
- **Structured and professional** (use headings, bullet points)
- **Insightful** (highlight trends, potential risks, and opportunities)
- **Concise but detailed** (avoid unnecessary repetition)

Generate a detailed report based on these indicators."""

social_media_prompt = """Generate a comprehensive report analyzing the social media and sentiment trends for {share_name} share over the specified date range. The report should include:  

1. **Social Media Insights**  
   - Summarize key trends in social media discussions, particularly on Reddit.  
   - If no significant discussions are found, mention potential reasons for the absence of data.  

2. **Sentiment Analysis**  
   - Identify positive, negative, and neutral sentiment trends during the period.  
   - Highlight peak sentiment days and provide potential reasons behind major sentiment changes.  
   - Include numerical sentiment scores and engagement levels where applicable.  

3. **Implications for Traders and Investors**  
   - Explain how sentiment trends can impact investment decisions.  
   - Discuss whether the overall sentiment leans positive or negative.  
   - Provide recommendations or observations based on sentiment fluctuations.  

Ensure the report is structured clearly with relevant section headings and concise, data-driven insights."  

---

### **Prompt Information Likely Provided to the LLM:**  
- **Date Range:** November 4, 2024 – November 17, 2024  
- **Social Media Data Source:** Reddit  
- **Sentiment Scores for AAPL:**  
  - November 15: 0.5445  
  - November 11: 0.426  
  - November 12: -0.201  
  - November 4: -0.141  
  - Other dates with moderate or neutral sentiment  
- **Engagement Data:**  
  - Highest engagement on November 6 (score: 0.0756)  
- **Additional Context:**  
  - If no social media data is found, explain the possible reasons.  
  - Frame sentiment trends in the context of potential trading/investing insights.  

Would you like me to refine this further or tailor it for a specific use case?"""