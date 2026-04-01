# Import libraries

import requests
from bs4 import BeautifulSoup
import datetime
import time
import sqlite3

# Initialize sql db connection
conn = sqlite3.connect("main.db")
cur = conn.cursor()

# Create table if it doesnt exists
cur.execute("CREATE TABLE IF NOT EXISTS tf2(date, st_pcount, tw_cas, tw_cmm, tw_cmp, tw_tot)")



# Steam variables

st_API_KEY = "YOUR_STEAM_API_KEY"
st_APP_ID = 440  # TF2

st_url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"

st_params = {
    "appid": st_APP_ID,
    "key": st_API_KEY
}

# Teamwork.tf variables

tw_url = "https://teamwork.tf/community/statistics"

tw_headers = {
    "User-Agent": "Mozilla/5.0"
}

# Function to ingest Valve player count in TF2
def request_steam():
    try:
        # Make request
        response = requests.get(st_url, params=st_params)
        # Store data
        data = response.json()
        # Get player count
        player_count = data["response"]["player_count"]

        return player_count
    except Exception as e:
        print(e)
        return None

# Function to ingest in-server player count from Teamwork.tf 
def request_tw():
    try:
        # Make request
        res = requests.get(tw_url, headers=tw_headers)
        res.raise_for_status()

        # Webscraping html
        soup = BeautifulSoup(res.text, "html.parser")

        # Empty dict to store data
        data = {}

        # Find all rows in tables
        rows = soup.select("table tr")

        # From html data, select values for 
        for row in rows:
            cols = row.find_all(["td", "th"])
            text = cols[0].get_text(strip=True)
            if text in {"Casual", "Community", "Competitive"}:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                clean_value = value.replace(" player(s)", "").replace(",", "")

                data[key] = clean_value

        return data
    except Exception as e:
        print(e)
        return None


def main():
    while True:
        try:
            # Create timestamp
            date = datetime.datetime.now().isoformat()
            
            # Call functions
            st_pcount = request_steam()
            tw_pcount = request_tw()
            # Seperate values
            tw_cas = int(tw_pcount["Casual"])
            tw_cmm = int(tw_pcount["Community"])
            tw_cmp = int(tw_pcount["Competitive"])
            # Calculate total in-server player count 
            tw_tot = tw_cas + tw_cmm + tw_cmp
            # Add row to DB
            cur.execute("INSERT INTO tf2 (date, st_pcount, tw_cas, tw_cmm, tw_cmp, tw_tot) VALUES (?,?,?,?,?,?)", (date, st_pcount, tw_cas, tw_cmm, tw_cmp, tw_tot))
            conn.commit()
            # Print for diagnostics
            print(f"Data added: {date, st_pcount, tw_cas, tw_cmm, tw_cmp, tw_tot} ")
        except Exception as e:
            print(f"Error: {e}")

        # Sample every 15 minutes 
        time.sleep(900)

# Call main function
main()

