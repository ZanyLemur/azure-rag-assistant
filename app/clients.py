from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from openai import AzureOpenAI

from app import config

credential = DefaultAzureCredential()

token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

openai_client = AzureOpenAI(
    azure_endpoint=config.OPENAI_ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2024-10-21",  # check the current API version in the docs
)

search_client = SearchClient(
    endpoint=config.SEARCH_ENDPOINT,
    index_name=config.SEARCH_INDEX,
    credential=credential,
)