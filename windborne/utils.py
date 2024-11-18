import time
import requests
import boto3
from datetime import datetime
from .api import get_observations

def poll_observations(interval=60, since=None):
    # Default interval to 60 seconds if not provided
    since_timestamp = since if since else 0
    has_next_page = True

    while has_next_page:
        observations_page = get_observations(since=since_timestamp)
        print(f"Fetched {len(observations_page['observations'])} observations")

        if not observations_page.get('has_next_page', False):
            print("---------------------------------------------------")
            print("\nYour latest observations doesn't have a next page.")
            print("---------------------------------------------------")
            print(f"Sleeping for {interval} seconds")
            time.sleep(interval)

        since_timestamp = observations_page.get('next_since', since_timestamp)


def sync_to_s3(data, bucket_name, object_name):
    s3 = boto3.client("s3")
    s3.put_object(Body=str(data), Bucket=bucket_name, Key=object_name)