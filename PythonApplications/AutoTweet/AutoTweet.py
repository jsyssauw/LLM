import tweepy
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import time

DEBUG_MODE = True

load_dotenv()

BEARER_TOKEN = os.getenv('X_BEARER_TOKEN')

# SMTP server and port for mailprovider.
SMTP_SERVER = "mail.stackmail.com"  
SMTP_PORT = 465  # SSL port typically
    
# Provide your email creds (replace with environment variables in practice)
EMAIL_SENDER = "test@syssauw.com"

EMAIL_PASSWORD = os.getenv('TESTSYSSAUW_PWD')
# Email credentials (Replace with your details)
if DEBUG_MODE:
    print("Email pwd: ", EMAIL_PASSWORD)
    print("X Bearer Token: ", BEARER_TOKEN)


EMAIL_RECEIVER = "jan.syssauw@syssauw.com"
## https://developer.x.com/en/portal/dashboard
# Twitter username that you want to get the posts from 
TWITTER_USERNAME = "sama"

def get_latest_tweets(username, count=5):
    """Fetch latest tweets from a specified Twitter account."""
    client = tweepy.Client(bearer_token=BEARER_TOKEN)
    
    # Get user ID from username
    user = client.get_user(username=username)
    user_id = user.data.id
    
    # Fetch latest tweets
    try:
        tweets = client.get_users_tweets(id=user_id, max_results=count, tweet_fields=["created_at"])
    except tweepy.errors.TooManyRequests:
        ## just try once to get the tweets, if that attempts fails, error.
        print("Rate limit exceeded. Waiting 15 minutes before retrying...")
        time.sleep(15 * 60)  # Wait 15 minutes (900 seconds)
        tweets = client.get_users_tweets(id=user_id, max_results=count, tweet_fields=["created_at"])

    tweet_list = []
    for tweet in tweets.data:
        tweet_list.append(f"{tweet.created_at}: {tweet.text}")
    
    return tweet_list

def send_email(subject, body):
    """Send an email with the latest tweets from Sam Altman."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    
    msg.attach(MIMEText(body, "plain"))
    if DEBUG_MODE:
        print("Sending Starts: ....")
        print("Email: ", msg)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    
def main():
    """Main function to fetch tweets and send via email."""
    tweets = get_latest_tweets(TWITTER_USERNAME)
    
    if tweets:
        email_body = "\n\n".join(tweets)
        if DEBUG_MODE:
            print("Email: ",email_body)
        send_email(f"Latest Tweets from {TWITTER_USERNAME}", email_body)
        print("Email sent successfully!")
    else:
        print("No tweets found.")

if __name__ == "__main__":
    main()
