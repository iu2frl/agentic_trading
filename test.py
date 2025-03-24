from agents.utils.analyst_utils import SocialMedia, X
from pprint import pprint

if __name__ == "__main__":
    #####################################################################################################################3
    # socialmedia = SocialMedia(
    #     start_date="2024-01-01",
    #     end_date="2024-03-29"
    # )

    # socialmedia.calculate_sentiment_scores(share_name="Tata Consultancy Services Ltd", share_symbol="TCS")




    # from ntscraper import Nitter

    # scraper = Nitter(log_level=1, skip_instance_check=False)


    # nitter_out = scraper.get_tweets(
    #     "TCS share", 
    #     mode='term',
    #     since = "2024-01-01",
    #     until = "2024-03-29"
    #     )
    
    # tweets = nitter_out['tweets'] # list of tweets

    # for tweet in tweets:
    #     text= tweet['text']
    
    
    # bezos_tweets = scraper.get_tweets("JeffBezos", mode='user')
    # print(bezos_tweets)

    x_api = X(
        start_date="2024-01-01",
        end_date="2024-03-29"
    )
    
    tweets = x_api.search_posts_in_date_range(
        share_name="Tata Consultancy Services",
        share_symbol="TCS",
        # force_scrape=True
    )

    socialmedia = SocialMedia(
        start_date="2024-01-01",
        end_date="2024-03-29",
    )
    df = socialmedia.get_posts("TCS")
    print(df.head(20))