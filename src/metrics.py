

from datetime import datetime
import json
import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()

token = os.environ["token"]
url = "https://api.github.com/graphql"
repositories = []

query = """
query ($after: String) {
  repository(owner: "donnemartin", name: "system-design-primer") {
    pullRequests(first: 100, states: [MERGED,CLOSED], after: $after) {
      nodes {
        title
        url
        author {
          login
        }
        body
        createdAt
        mergedAt
        closedAt
        additions
        deletions
        participants {
          totalCount
        }
        comments {
          totalCount
        }
        files {
          totalCount
        }
        state
        reviews {
          totalCount
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

variables = {
    "after": None
}


headers = {"Authorization": "Bearer " + token}
while True:
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    data = json.loads(response.text)

    page_info = data['data']['repository']['pullRequests']['pageInfo']

    prs = data['data']['repository']['pullRequests']['nodes']
    for pr in prs:
        title = pr["title"]
        created_at = datetime.strptime(
                pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
        if pr["state"] == 'CLOSED':
            closed_at = datetime.strptime(pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
            review_time = (closed_at - created_at).total_seconds() / 3600
        else:
            merged_at = datetime.strptime(pr['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
            review_time = (merged_at - created_at).total_seconds() / 3600

    if not page_info['hasNextPage']:
        break

    variables['after'] = page_info['endCursor']
        



