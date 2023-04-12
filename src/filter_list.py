
import pandas as pd

def filter_repos_csv():
    df = pd.read_csv('resultados.csv')
    df = df[df['PRs Aprovados ou Fechados'] >= 100]
    df.head(200).to_csv('resultados_filtrados.csv', index=False)

filter_repos_csv()