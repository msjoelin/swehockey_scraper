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



def getGames(id_list):
    """
    Get all games from list of ids
    Output is dataframe with all games 
    """
    
    data=[]
   
    # Loop over all players
    for index, schedule_id in enumerate(id_list):
    
        url = 'http://stats.swehockey.se/ScheduleAndResults/Schedule/' + schedule_id
        print('Collects data from ' + url)
         
        df_games = pd.read_html(url)[2]
                 
        # Select relevant columns and rename (structure of table changed from season 18/19)        
        if df_games.columns[0][1]=='Round':
            df_games = df_games.iloc[:,[1,2,3,4,5]]
        else:
            df_games = df_games.iloc[:,[1,3,4,5,6]]

        df_games.columns = ['date', 'game', 'score', 'periodscore', 'spectators']
        
        # Adjust date column; remove time and fill empty rows with previous value
        df_games['date'] = df_games['date'].map(lambda x: str(x)[:-5])    
        df_games['date'] = df_games['date'].replace('', np.nan).ffill(axis=0)
        
        df_games['schedule_id'] = schedule_id
            
        # Extract game-id (found in href - javascript)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        address_class = soup.find_all('td', {"class": ["tdOdd standardPaddingTop", "tdNormal standardPaddingTop", 
                                                       "tdOdd paddingTop", "tdNormal paddingTop"]})
        all_a = []
        for row in address_class:
            if row.find('a') is not None:
                all_a.append(str(row.find('a')))
                
        df_id = pd.DataFrame(all_a, columns=['href']) 
         
        #Split string, only keep ID
        df_id['href'] = df_id['href'].str.split(">", n=0, expand=True)
        df_id['href'] = df_id['href'].str.extract('(\d+)')
    
        if df_id.shape[0] == df_games.shape[0]:
            df_games['game_id'] = df_id['href']
        else:
            Print("Couldnt extract correct number of IDs")
            df_games['game_id'] = np.nan
            
        data.append(df_games)
        
        print(schedule_id, " collected")
          
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
    elif ((teamname=='Färjestad BKMatchstart ca 20.30') |(teamname=='Färjestads BK')) :
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

    df_games[['home', 'away']] = df_games.game.str.split('-', expand = True, n=2)
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
    Takes outout from cleanGames and returns dataframe 
    with row by row by team. This is for analysis 
    """
    
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
    
    # Lag games and results
    df_teams = df_teams.sort_values(['team', 'date']).reset_index(drop=True)

    df_teams['result_L1'] = df_teams.groupby(['team', 'season'])['result'].shift(periods=1)
    df_teams['result_L2'] = df_teams.groupby(['team', 'season'])['result'].shift(periods=2)
    df_teams['result_L3'] = df_teams.groupby(['team', 'season'])['result'].shift(periods=3)
    df_teams['result_L4'] = df_teams.groupby(['team', 'season'])['result'].shift(periods=4)
    df_teams['result_L5'] = df_teams.groupby(['team', 'season'])['result'].shift(periods=5)
    
    df_teams['win'] = 0
    df_teams.loc[df_teams['result'] == 'win', 'win'] = 1
    df_teams['draw'] = 0
    df_teams.loc[df_teams['result'] == 'draw', 'draw'] = 1
    df_teams['lost'] = 0
    df_teams.loc[df_teams['result'] == 'lost', 'lost'] = 1   
    
    df_teams['win_R5'] = df_teams.groupby(['team', 'season'])['win'].rolling(5, min_periods=1).mean().values
    df_teams['win_R5'] =df_teams.groupby(['team', 'season'])['win_R5'].shift(fill_value=0)
    
    df_teams['draw_R5'] = df_teams.groupby(['team', 'season'])['draw'].rolling(5, min_periods=1).mean().values
    df_teams['draw_R5'] =df_teams.groupby(['team', 'season'])['draw_R5'].shift(fill_value=0)
    
    df_teams['lost_R5'] = df_teams.groupby(['team', 'season'])['lost'].rolling(5, min_periods=1).mean().values
    df_teams['lost_R5'] =df_teams.groupby(['team', 'season'])['lost_R5'].shift(fill_value=0)
    
    # Matchday
    df_teams['matchday'] = df_teams.groupby(['team', 'season']).cumcount()+1
    df_teams['matchday_h_a'] = df_teams.groupby(['team', 'season', 'h_a']).cumcount() +1 
     
    # Scored
    df_teams['scored_avg_R5'] = df_teams.groupby(['team', 'season'])['score_team'].rolling(5, min_periods=1).mean().values
    df_teams['scored_avg_R5'] =df_teams.groupby(['team', 'season'])['scored_avg_R5'].shift(fill_value=0)
    df_teams['conceded_avg_R5'] = df_teams.groupby(['team', 'season'])['score_opponent'].rolling(5, min_periods=1).mean().values
    df_teams['conceded_avg_R5'] =df_teams.groupby(['team', 'season'])['conceded_avg_R5'].shift(fill_value=0)
    
    df_teams['scored_cum'] = df_teams.groupby(['team', 'season'])['score_team'].cumsum()
    df_teams['scored_cum_prev'] =df_teams.groupby(['team', 'season'])['scored_cum'].shift(fill_value=0)
    df_teams['scored_cum_prev_avg'] = df_teams['scored_cum_prev'] / (df_teams['matchday']-1)
    
    df_teams['conceded_cum'] = df_teams.groupby(['team', 'season'])['score_opponent'].cumsum()
    df_teams['conceded_cum_prev'] =df_teams.groupby(['team', 'season'])['conceded_cum'].shift(fill_value=0)
    df_teams['conceded_cum_prev_avg'] = df_teams['conceded_cum_prev'] / (df_teams['matchday']-1)
    
    # H2H
    df_teams['H2H_W'] = df_teams.groupby(['team', 'opponent'])['win'].cumsum()
    df_teams['H2H_W'] =df_teams.groupby(['team', 'opponent'])['H2H_W'].shift(fill_value=0)
    df_teams['H2H_D'] = df_teams.groupby(['team', 'opponent'])['draw'].cumsum()
    df_teams['H2H_D'] =df_teams.groupby(['team', 'opponent'])['H2H_D'].shift(fill_value=0)
    df_teams['H2H_L'] = df_teams.groupby(['team', 'opponent'])['lost'].cumsum()
    df_teams['H2H_L'] =df_teams.groupby(['team', 'opponent'])['H2H_L'].shift(fill_value=0)
    
    # Normalize values
    df_teams[['H2H_W', 'H2H_D', 'H2H_L']] =df_teams[['H2H_W', 'H2H_D', 'H2H_L']].div(df_teams[['H2H_W', 'H2H_D', 'H2H_L']].sum(axis=1),axis=0).fillna(0)
    
    # Points collected
    df_teams['points'] = 0
    df_teams.loc[df_teams['result'] == 'win', 'points'] = 3
    df_teams.loc[(df_teams['result_p4'] == 'win') | (df_teams['result_p5'] == 'win'), 'points'] = 2
    df_teams.loc[(df_teams['result_p4'] == 'lost') | (df_teams['result_p5'] == 'lost'), 'points'] = 1
    
    df_teams['points_cum'] = df_teams.groupby(['team', 'season'])['points'].cumsum()
    df_teams['points_cum_prev'] =df_teams.groupby(['team', 'season'])['points_cum'].shift(fill_value=0)    
    df_teams['points_cum_prev_avg'] = df_teams['points_cum_prev'] / (df_teams['matchday']-1)
 
    df_teams['points_cum_h_a'] = df_teams.groupby(['team', 'season', 'h_a'])['points'].cumsum()
    df_teams['points_cum_h_a_prev'] =df_teams.groupby(['team', 'season', 'h_a'])['points_cum_h_a'].shift(fill_value=0)
    df_teams['points_cum_h_a_prev_avg'] = df_teams['points_cum_h_a_prev'] / (df_teams['matchday_h_a']-1)
    
 
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
        
        print('collected ', index, game_id)
            
    games=pd.concat(data)
    gamessummary = pd.concat(datasummary)

    
    return games, gamessummary
