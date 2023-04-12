

from datetime import datetime
import json
import requests
import os
from dotenv import load_dotenv
import csv
import markdown


def get_time_diff(start_time, end_time):
    diff_seconds = (end_time - start_time).total_seconds()
    diff_hours, diff_minutes = divmod(diff_seconds, 3600)
    diff_minutes //= 60
    return "{:.0f}h{:02.0f}m".format(diff_hours, diff_minutes)

load_dotenv()

token = os.environ["token"]
url = "https://api.github.com/graphql"
repositories = []

query = """
query ($after: String) {
  repository(owner: "donnemartin", name: "system-design-primer") {
    pullRequests(first: 100, states: [MERGED,CLOSED], after: $after) {
      nodes {
        id
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
        state
        participants {
          totalCount
        }
        comments {
          totalCount
        }
        files {
          totalCount
        }
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
row_data = []
while True:
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    data = json.loads(response.text)
    if response.status_code == 200:
        page_info = data['data']['repository']['pullRequests']['pageInfo']

        prs = data['data']['repository']['pullRequests']['nodes']
        for pr in prs:
            title = pr["title"]
            created_at = datetime.strptime(
                    pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
            if pr["state"] == 'CLOSED':
                closed_at = datetime.strptime(pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
                review_time = get_time_diff(created_at, closed_at)
            else:
                merged_at = datetime.strptime(pr['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
                review_time = get_time_diff(created_at, merged_at)
            
            markdown_body = markdown.markdown(pr['body'])
            with open("src/pull_request_body.md", "w") as file:
                file.write(markdown_body)
            with open("src/pull_request_body.md", "r") as file:
                content = file.read()
                num_caracteres = len(content)
            num_arquivos = pr["files"]["totalCount"]
            num_additions = pr["additions"]
            num_deletions = pr["deletions"]
            num_participants = pr["participants"]["totalCount"]
            num_comments = pr["comments"]["totalCount"]
            pr_id = pr["id"]
            state = pr["state"]
            name_owner = "donnemartin/system-design-primer" # temporario

            row = [name_owner, pr_id, title, state, review_time, num_caracteres, num_arquivos, num_additions, num_deletions, num_participants, num_comments]
            row_data.append(row)
        if not page_info['hasNextPage']:
            break
    else:
        continue
      

    variables['after'] = page_info['endCursor']
        
  
with open('metricas.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['name_owner', 'pr_id', 'title', 'state', 'review_time', 'num_caracteres', 'num_arquivos', 'num_additions', 'num_deletions', 'num_participants', 'num_comments'])
    for row in row_data:
        writer.writerow(row)


