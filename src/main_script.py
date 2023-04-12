
import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()

token = os.environ["token"]
url = "https://api.github.com/graphql"
repositories = []


query = '''
query {
  search(query: "stars:>100 sort:stars-desc", type: REPOSITORY, first: 20, after: null) {
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        url
        pullRequests(states: [MERGED, CLOSED]) {
          totalCount
        }
        
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
'''

headers = {"Authorization": "Bearer " + token}
count = 0
data = []
cursor = None 

while count < 1000:
    if cursor:
        query_with_cursor = query.replace('after: null', 'after: "%s"' % cursor)

        response = requests.post(url, json={"query": query_with_cursor}, headers=headers)
    else:
        response = requests.post(url, json={"query": query}, headers=headers)
        
    if response.status_code == 200:
        repos = response.json()['data']['search']['nodes']
        page_info = response.json()['data']['search']['pageInfo']
        cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
        for repo in repos:
            count += 1
            name = repo['nameWithOwner']
            stars = repo['stargazerCount']
            repo_url = repo['url']
            num_pr_merged_or_closed = repo['pullRequests']['totalCount']
            
            row = [count, name, stars, repo_url, num_pr_merged_or_closed, ]
            data.append(row)
        print(count)
    else:
        continue

with open('resultados.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Número', 'Nome', 'Estrelas', 'url', 'PRs Aprovados ou Fechados'])
    for row in data:
        writer.writerow(row)

