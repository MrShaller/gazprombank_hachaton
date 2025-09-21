from scripts.prepare_dataset import main as prepare_dataset
from scripts.match_topics.topic_matcher_all import main as topic_matcher
from scripts.sentiments.sentiment_all import main as sentiment


if __name__ == "__main__":
    #prepare_dataset()

    topic_matcher()

    sentiment()


