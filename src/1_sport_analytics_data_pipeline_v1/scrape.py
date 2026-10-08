import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# BBC can block or serve a different page to requests without a browser
# User-Agent (common on cloud runners like GitHub Actions)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def league_table():
    '''
        I have used and asked claude code to check the premier-league table in the url and scrape the data from it. The code is working fine and I have tested it. It is returning the league table as a pandas dataframe.
        
    '''

    # the page link we want to extract data from
    url = "https://www.bbc.com/sport/football/premier-league/table"
    headers = ['Position']
    page  = requests.get(url, headers=HEADERS, timeout=30)
    page.raise_for_status()
    page.encoding = 'utf-8'
    soup = BeautifulSoup(page.text, 'html.parser')

    # find the table
    table = soup.find('table', {'data-testid': 'football-table'})
    if table is None:
        raise RuntimeError(f"League table not found on {url} (page layout changed or request blocked)")


    for i in table.find_all('th'):
        title =i.text
        headers.append(title)

    # create a dataframe
    league_table = pd.DataFrame(columns = headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')

        # the "Team" cell packs the rank number, crest and team name together,
        # so pull the rank and the (screen-reader) team name out separately
        team_cell = row_data[0]
        rank = team_cell.find('span', class_='ssrcss-1mnw0cb-Rank').text
        team = team_cell.find('span', class_='visually-hidden').text

        row = [rank, team] + [i.text for i in row_data[1:]]
        length = len(league_table)
        league_table.loc[length] = row
    return league_table





def top_scorers():
    '''
    I have used and asked claude code to check the top scorers table in the url and scrape the data from it. The code is working fine and I have tested it. It is returning the top scorers table as a pandas dataframe.
    
    '''

    # the page link we want to extract data from
    url = "https://www.bbc.com/sport/football/premier-league/top-scorers"
    page  = requests.get(url, headers=HEADERS, timeout=30)
    page.raise_for_status()
    # BBC doesn't declare a charset, so requests falls back to Latin-1 and
    # accented names get garbled (e.g. "JoÃ£o"); the page is actually UTF-8
    page.encoding = 'utf-8'
    soup = BeautifulSoup(page.text, 'html.parser')

    # find the table
    table = soup.find('table', {'data-testid': 'sport-table'})
    if table is None:
        raise RuntimeError(f"Top scorers table not found on {url} (page layout changed or request blocked)")

    # BBC renders every stat column twice - once with a full label for desktop
    # and once abbreviated for mobile - and both copies hold the same value,
    # so we only keep one <th>/<td> per stat (indices into the raw columns)
    stat_columns = [2, 4, 6, 8, 9, 11, 12, 13]

    def header_text(th):
        # prefer the visible label; fall back to the screen-reader-only one
        visible = th.find('span', attrs={'aria-hidden': 'false'})
        if visible:
            return visible.get_text(strip=True)
        hidden = th.find('span', class_='visually-hidden')
        return hidden.get_text(strip=True) if hidden else th.get_text(strip=True)

    all_headers = table.find_all('th')
    headers = ['Position', 'Player', 'Team'] + [header_text(all_headers[i]) for i in stat_columns]

    # create a dataframe
    top_scorers_table = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        if not row_data:
            continue

        rank = row_data[0].get_text(strip=True)

        # the "Name" cell packs the player and team together (duplicated for
        # desktop/mobile), so pull them out of the first player/team pair
        info_block = row_data[1].find('div', attrs={'role': 'text'})
        name_divs = info_block.find_all('div', recursive=False)
        player = name_divs[0].get_text(strip=True)
        team = name_divs[1].get_text(strip=True)

        stats = [row_data[i].get_text(strip=True) for i in stat_columns]

        row = [rank, player, team] + stats
        length = len(top_scorers_table)
        top_scorers_table.loc[length] = row
    return top_scorers_table


# if you need to run the functions and see the output, you can uncomment the following lines:
# if __name__ == "__main__":
#     league_table_df = league_table()
#     top_scorers_df = top_scorers()

#     print(league_table_df)
#     print(top_scorers_df)