import requests
import pandas as pd


# TheSportsDB is a free public API. "3" is their public test key, so no signup
# and no secret to protect. Docs: https://www.thesportsdb.com/free_sports_api
BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"


def premier_league_teams():
    '''
    Ingests Premier League team details from the free TheSportsDB REST API and
    returns them as a pandas dataframe (same shape of output as the scrape.py
    functions, so it can be pushed to Azure Blob Storage the same way).

    Note: the free key only returns a subset (10) of the 20 teams.
    '''

    url = f"{BASE_URL}/search_all_teams.php"
    params = {"l": "English Premier League"}

    # call the API; timeout stops us hanging forever, raise_for_status fails
    # loudly on a 4xx/5xx instead of silently parsing an error page
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    # the API answers with JSON: {"teams": [ {...}, {...} ]}
    teams = response.json().get("teams") or []

    df = pd.DataFrame(teams)

    # the raw payload has ~70 columns (descriptions in many languages, social
    # links, artwork...) - keep only the ones useful for analytics
    columns = {
        "idTeam": "Team ID",
        "strTeam": "Team",
        "strTeamShort": "Short Name",
        "intFormedYear": "Formed",
        "strStadium": "Stadium",
        "strLocation": "Location",
        "strCountry": "Country",
        "strWebsite": "Website",
    }
    df = df[[c for c in columns if c in df.columns]].rename(columns=columns)
    return df


# if you need to run the function and see the output, you can uncomment the following lines:
# if __name__ == "__main__":
#     print(premier_league_teams())
