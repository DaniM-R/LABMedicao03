

from datetime import datetime
import json
import random
from time import sleep
import pandas as pd
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


def get_remaining_requests(token):
    headers = {'Authorization': f'token {token}'}
    response = requests.get(
        'https://api.github.com/rate_limit', headers=headers)
    if response.status_code == 200:
        remaining_requests = response.json()['rate']['remaining']
        return remaining_requests
    else:
        print('Erro ao recuperar número de requisições restantes')


def get_data(nameWithOwner):
    load_dotenv()

    tokens = [os.environ["token1"], os.environ["token2"]]
    token = random.choice(tokens)

    url = "https://api.github.com/graphql"

    query = """
    query ($after: String, $owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
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
        "after": None,
        "owner": nameWithOwner.split("/")[0],
        "name": nameWithOwner.split("/")[1]
    }

    headers = {"Authorization": "Bearer " + token}
    row_data = []
    while True:
        print("1 * REQUISIÇÃO ")
        sleep(0.9)
        response = requests.post(
            url, json={"query": query, "variables": variables}, headers=headers)

        data = json.loads(response.text)
        print(response.content)

        if response.status_code == 200:
            print("2 * MANIPULAÇÃO DOS DADOS (STATUS CODE = 200)")
            page_info = data['data']['repository']['pullRequests']['pageInfo']

            prs = data['data']['repository']['pullRequests']['nodes']
            for pr in prs:
                m = pd.read_csv("metricas2.csv")
                if pr["id"] in m:
                    continue
                if pr["reviews"]["totalCount"] < 1:
                    continue
                num_reviews = pr["reviews"]["totalCount"]
                title = pr["title"]
                created_at = datetime.strptime(
                    pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')

                if pr["state"] == 'CLOSED':
                    closed_at = datetime.strptime(
                        pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
                    review_time = get_time_diff(created_at, closed_at)
                    if (created_at - closed_at).seconds < 3600:
                        continue
                else:
                    merged_at = datetime.strptime(
                        pr['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
                    review_time = get_time_diff(created_at, merged_at)
                    if (created_at - merged_at).seconds < 3600:
                        continue

                markdown_body = markdown.markdown(pr['body'])
                with open("src/pull_request_body.md", "w", encoding="utf-8") as file:
                    file.write(markdown_body)
                with open("src/pull_request_body.md", "r", encoding="utf-8") as file:
                    content = file.read()
                    num_caracteres = len(content)
                num_arquivos = pr["files"]["totalCount"]
                num_additions = pr["additions"]
                num_deletions = pr["deletions"]
                num_participants = pr["participants"]["totalCount"]
                num_comments = pr["comments"]["totalCount"]
                pr_id = pr["id"]
                state = pr["state"]
                name_owner = nameWithOwner

                row = [name_owner, pr_id, title, state, review_time, num_reviews, num_caracteres,
                       num_arquivos, num_additions, num_deletions, num_participants, num_comments]
                if row in row_data:
                    continue
                row_data.append(row)
            if not page_info['hasNextPage']:
                break
        else:
            print(f"2 * ERRO {response.status_code}")
            if response.status_code >= 500:
                token = random.choice(tokens)
            continue

        variables['after'] = page_info['endCursor']

    with open('metricas2.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        for row in row_data:
            writer.writerow(row)
    return


def main():
    df = pd.read_csv("resultados_filtrados.csv")
    for index, row in df.iterrows():
        get_data(row["Nome"])


main()
