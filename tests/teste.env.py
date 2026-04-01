from dotenv import load_dotenv
import os

load_dotenv()

print("API URL:", os.getenv("AWS_FV_GRAPHQL_URL"))
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_NAME:", os.getenv("DB_NAME"))
print("AUTH_METHOD:", os.getenv("AUTH_METHOD"))
