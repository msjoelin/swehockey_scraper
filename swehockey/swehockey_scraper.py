# -*- coding: utf-8 -*-
"""
Functions for collecting data from swehockey
"""

import numpy as np
import pandas as pd
from bs4  import BeautifulSoup
import requests
import time
from datetime import datetime
import re



def getGames(season_id):
    """
    Get all games from list of season ids. 
    Season ID should be a pd series. 
    Output is dataframe with all games , including results, venue, date, period and the game id 
    """   
    data=[]
   
    # Loop over all ids in the list
    for index, schedule_id in enumerate(season_id):
    
        url = 'http://stats.swehockey.se/ScheduleAndResults/Schedule/' + schedule_id
        
        # Read in the table from the list 
        df_games = pd.read_html(url)[2]
        df_games.columns = df_games.columns.get_level_values(1)
                 
        # Initiate a new cleaned dataframe to store the result when we have found relevant data
        df_games_cleaned=pd.DataFrame()
        
        # Find the first column with a date format (could be with timestamp after)
        date_pattern = r'^\d{4}-\d{2}-\d{2}'

        # Loop through columns and assign the column to the new df 
        for i, col in enumerate(df_games.columns):
            if re.match(date_pattern, str(df_games[col].iloc[0])):
                df_games_cleaned['date_col'] = df_games[[col]]
                break


        # Find the first column after the date column which has more than 8 letters (this should ensure we have the game here)
        # Also grab the 4 nextcoming columns 

        for i, col in enumerate(df_games.columns):
            if len(re.findall(r'[a-zA-Z]', str(df_games[col].iloc[0])))>=5:
                # Grab the current column and the next 3 columns
                df_games_cleaned['game'] = df_games.iloc[:, i]
                df_games_cleaned['score'] = df_games.iloc[:, i+1]
                df_games_cleaned['periodscore'] = df_games.iloc[:, i+2]
                df_games_cleaned['spectators'] = df_games.iloc[:, i+3]
                break

        # Adjust the date column -> clean away datatime, and if no date value, fill with previous non-null value
        df_games_cleaned['date'] = pd.to_datetime(df_games_cleaned['date_col'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        df_games_cleaned['date'] = df_games_cleaned['date'].replace('', pd.NA).ffill().fillna('')

        df_games_cleaned = df_games_cleaned.drop(columns=['date_col'])


        # Assign the schedule id to the dataframe
        df_games_cleaned['schedule_id'] = schedule_id
            
        # Extract the game-id, which is found in href - javascript
        agent = {"User-Agent":"Mozilla/5.0"}
        page = requests.get(url, headers=agent)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        address_class = soup.find_all('td', {"class": ["tdOdd standardPaddingTop", "tdNormal standardPaddingTop", 
                                                       "tdOdd paddingTop", "tdNormal paddingTop"]})
        all_a = []
        for row in address_class:
            if row.find('a') is not None:
                all_a.append(str(row.find('a')))
                
        df_id = pd.DataFrame(all_a, columns=['href']) 
         
        #Extract the game id from the href column 
        df_id['game_id'] =  df_id['href'].str.extract(r'/Game/Events/(\d+)')
        
        # Add the games 
        df_games_cleaned=pd.concat([df_games_cleaned,df_id['game_id']], axis=1)
      
        data.append(df_games_cleaned)

        print('Schedule ID ' + schedule_id + ' added with ' + str(len(df_games_cleaned)) + ' rows')
                  

    games=pd.concat(data)
    
    return games



def getPeriodWinner(homescore, awayscore):
    """
    Function to determine periodwinner 
    """
    if (homescore==awayscore):
        return 'draw'
    elif (homescore>awayscore):
        return 'home'
    elif (homescore<awayscore):
        return 'away'
    else:
        return None


def replaceTeamName(teamname):
    """
    Replace teamnames that are not consistently named
    """
    
    if ((teamname == 'A I K IF') | (teamname == 'AIK IF')):
        return 'AIK'
    elif (teamname=='Bofors IK Karlskoga'):
        return 'Bofors IK'
    elif ((teamname=='Färjestad BKMatchstart ca 20.30') |(teamname=='Färjestad BK Matchstart ca 20.30') |(teamname=='Färjestads BK')) :
        return 'Färjestad BK'
    elif (teamname=='Linköpings HC'):
        return 'Linköping HC'
    elif (teamname=='VIK Västerås HK'):
        return 'Västerås IK'
    else:
        return teamname


def cleanGames(df_games):
    """
    Clean output from getGames into data for analysis
    """

    df_games[['home', 'away']] = df_games.game.str.split(' - ', expand = True, n=2)
    df_games[['score_home', 'score_away']] = df_games.score.str.split('-', expand = True, n=2)
    
    df_games.columns = df_games.columns.str.strip()
    
    df_games['home'] = df_games['home'].str.strip()
    df_games['away'] = df_games['away'].str.strip()
    
    df_games['home'] = df_games.apply(lambda x: replaceTeamName(x.home), axis=1)
    df_games['away'] = df_games.apply(lambda x: replaceTeamName(x.away), axis=1)
    

    # Periodscore 
    df_games['periodscore'] = df_games['periodscore'].str.strip('()')
    df_games[['p1score', 'p2score', 'p3score', 'p4score', 'p5score']] = df_games.periodscore.str.split(',', expand = True, n=4)
    
    df_games[['p1score_home', 'p1score_away']] = df_games.p1score.str.split('-', expand = True, n=2)
    df_games[['p2score_home', 'p2score_away']] = df_games.p2score.str.split('-', expand = True, n=2)
    df_games[['p3score_home', 'p3score_away']] = df_games.p3score.str.split('-', expand = True, n=2)
    df_games[['p4score_home', 'p4score_away']] = df_games.p4score.str.split('-', expand = True, n=2)
    df_games[['p5score_home', 'p5score_away']] = df_games.p5score.str.split('-', expand = True, n=2)
    
    cols_to_num = ['score_home', 'score_away', 'p1score_home', 'p1score_away',
                   'p2score_home', 'p2score_away', 'p3score_home', 'p3score_away',
                   'p4score_home', 'p4score_away', 'p5score_home', 'p5score_away']
    
    df_games[cols_to_num] = df_games[cols_to_num].apply(lambda x: x.str.strip())
    df_games[cols_to_num] = df_games[cols_to_num].apply(pd.to_numeric, errors='coerce')
    
    df_games.loc[pd.notna(df_games['p4score']), 'result'] = 'draw'
    df_games.loc[(df_games['score_home']>df_games['score_away']) & (df_games['result']!='draw'), 'result'] = 'home'
    df_games.loc[(df_games['score_home']<df_games['score_away']) & (df_games['result']!='draw'), 'result'] = 'away'
    
    df_games['result_p1'] = df_games.apply(lambda x: getPeriodWinner(x.p1score_home,x.p1score_away), axis=1)
    df_games['result_p2'] = df_games.apply(lambda x: getPeriodWinner(x.p2score_home,x.p2score_away), axis=1)
    df_games['result_p3'] = df_games.apply(lambda x: getPeriodWinner(x.p3score_home,x.p3score_away), axis=1)
    df_games['result_p4'] = df_games.apply(lambda x: getPeriodWinner(x.p4score_home,x.p4score_away), axis=1)
    df_games['result_p5'] = df_games.apply(lambda x: getPeriodWinner(x.p5score_home,x.p5score_away), axis=1)
    
    return df_games
       

def getTeamData(df_games):
    """
    Takes output from cleanGames and returns dataframe where each team has one row per game, so that we can calculate statistics
    """

    # Make two copies of the data, where we replace home resp away with "team" 
    df_home = df_games.copy()
    df_away = df_games.copy()
    
    df_home.columns = df_home.columns.str.replace("home", "team")
    df_home.columns = df_home.columns.str.replace("away", "opponent")
    df_home = df_home.replace('home', 'win')
    df_home = df_home.replace('away', 'lost')
    df_home['h_a'] = 'home'
    
    df_away.columns = df_away.columns.str.replace("away", "team")
    df_away.columns = df_away.columns.str.replace("home", "opponent")
    df_away = df_away.replace('away', 'win')
    df_away = df_away.replace('home', 'lost')
    df_away['h_a'] = 'away'
    
    df_teams = pd.concat([df_home, df_away]).reset_index(drop=True)
    
    # Sort values and set columns for win, draw and lost 1 and 0 
    df_teams = df_teams.sort_values(['team', 'date']).reset_index(drop=True)
    
    df_teams['win'] = 0
    df_teams.loc[df_teams['result'] == 'win', 'win'] = 1
    df_teams['draw'] = 0
    df_teams.loc[df_teams['result'] == 'draw', 'draw'] = 1
    df_teams['lost'] = 0
    df_teams.loc[df_teams['result'] == 'lost', 'lost'] = 1   

    # Calculate statistics for last 5 games for win, draw,lost, scored and conceded AHEAD of the game. SO, the played game is not included
    df_teams['pregame_L5_winratio'] = df_teams.groupby(['team', 'schedule_id'])['win'].apply(lambda x: x.rolling(window=5, min_periods=5).mean().shift(1)).reset_index(level=[0, 1], drop=True)
    df_teams['pregame_L5_drawratio'] = df_teams.groupby(['team', 'schedule_id'])['draw'].apply(lambda x: x.rolling(window=5, min_periods=5).mean().shift(1)).reset_index(level=[0, 1], drop=True)
    df_teams['pregame_L5_lostratio'] = df_teams.groupby(['team', 'schedule_id'])['lost'].apply(lambda x: x.rolling(window=5, min_periods=5).mean().shift(1)).reset_index(level=[0, 1], drop=True)
    
    df_teams['pregame_L5_avgscored'] = df_teams.groupby(['team', 'schedule_id'])['score_team'].apply(lambda x: x.rolling(window=5, min_periods=5).mean().shift(1)).reset_index(level=[0, 1], drop=True)
    df_teams['pregame_L5_avgconceded'] = df_teams.groupby(['team', 'schedule_id'])['score_opponent'].apply(lambda x: x.rolling(window=5, min_periods=5).mean().shift(1)).reset_index(level=[0, 1], drop=True)
    
    # Matchday counter
    df_teams['matchday'] = df_teams.groupby(['team', 'schedule_id']).cumcount()+1
    df_teams['matchday_h_a'] = df_teams.groupby(['team', 'schedule_id', 'h_a']).cumcount() +1 

    # Cumulative scored and conceded metrics 
    df_teams['scored_cum'] = df_teams.groupby(['team', 'schedule_id'])['score_team'].cumsum()
    df_teams['conceded_cum'] = df_teams.groupby(['team', 'schedule_id'])['score_opponent'].cumsum()
    df_teams['goal_difference_cum'] = df_teams['scored_cum'] - df_teams['conceded_cum'] 
    
    df_teams['pregame_scored_cum'] =df_teams.groupby(['team', 'schedule_id'])['scored_cum'].shift(fill_value=0)
    df_teams['pregame_conceded_cum'] =df_teams.groupby(['team', 'schedule_id'])['conceded_cum'].shift(fill_value=0)

    df_teams['pregame_avgscored_cum'] = df_teams['pregame_scored_cum'] / (df_teams['matchday']-1)
    df_teams['pregame_avgconceded_cum'] = df_teams['pregame_conceded_cum'] / (df_teams['matchday']-1)
        
    # Set points
    df_teams['points'] = 0
    df_teams.loc[df_teams['result'] == 'win', 'points'] = 3
    df_teams.loc[(df_teams['result_p4'] == 'win') | (df_teams['result_p5'] == 'win'), 'points'] = 2
    df_teams.loc[(df_teams['result_p4'] == 'lost') | (df_teams['result_p5'] == 'lost'), 'points'] = 1

    # Cumulative points metrics
    df_teams['points_cum'] = df_teams.groupby(['team', 'schedule_id'])['points'].cumsum()
    df_teams['pregame_points_cum'] =df_teams.groupby(['team', 'schedule_id'])['points_cum'].shift(fill_value=0)    
    df_teams['pregame_avgpoints'] = df_teams['pregame_points_cum'] / (df_teams['matchday']-1)
 
    df_teams['points_cum_h_a'] = df_teams.groupby(['team', 'schedule_id', 'h_a'])['points'].cumsum()
    df_teams['pregame_h_a_points_cum'] =df_teams.groupby(['team', 'schedule_id', 'h_a'])['points_cum_h_a'].shift(fill_value=0)
    df_teams['pregame_h_a_avgpoints'] = df_teams['pregame_h_a_points_cum'] / (df_teams['matchday_h_a']-1)
    
    # Assign the table position based on cumulative points
    df_teams['table_position_base'] = df_teams.groupby(['schedule_id', 'matchday'])['points_cum'].rank(ascending=False, method = 'min')
    # If we have same cumulative points, we rank on goaldifference 
    df_teams['table_position_goaldiff'] = df_teams.groupby(['schedule_id', 'matchday', 'table_position_base'])['goal_difference_cum'].rank(ascending=False, method = 'min')
    # Create the final rank by combining the base an goaldifference rank
    df_teams['table_position'] = df_teams['table_position_base'] + df_teams['table_position_goaldiff'] - 1 
    
    # Drop the helper table position columns
    df_teams = df_teams.drop(columns=['table_position_base', 'table_position_goaldiff'])

 
    return df_teams
    

    

def getGameData(game_id):
    """
    Takes list of game-ids and extracts all data.
    Return dataframe with event-information and one dataframe with a summary of all games
    """
    
    data=[]
    datasummary=[]
    
    for index, game_id in enumerate(game_id):
            
        url = 'http://stats.swehockey.se/Game/Events/' + game_id
        
        df_gamedata = pd.read_html(url)
        
        # Get relevant columns, rename and only keep rows with time (length: 5)
        df_gameevents = df_gamedata[5].iloc[:,[0,1,2,3,4]]
        
        df_gameevents.columns = ['time', 'event', 'team', 'players', 'on_ice']
        
        df_gameevents = df_gameevents[df_gameevents['time'].str.len()==5]
        df_gameevents['game_id'] = game_id
        
        # Get 
        df_gamesummary = df_gamedata[2].iloc[:,[1,2,5,6]]
        df_gamesummary = df_gamesummary.iloc[[1]]
        df_gamesummary.columns = ['shots_h', 'shots_h_period', 'shots_a', 'shots_a_period']
        df_gamesummary['league'] = df_gamedata[2].iloc[0,3]
        df_gamesummary['game_id'] = game_id
        
        data.append(df_gameevents)
        datasummary.append(df_gamesummary)
        
        #print('collected ', index, game_id)
            
    games=pd.concat(data)
    gamessummary = pd.concat(datasummary)

    
    return games, gamessummary
