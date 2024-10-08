# swehockey_scraper
This package can be used to collect data with web scraping from the page stats.swehockey.se. 
This is the website where the Swedish Icehockey Federation stores match statistics. 

This package is only for personal usage. 

I try to update this package in case something is changing. Any changes to the homepage structure means likely that functions needs to get updated as well. 
If you find something, please get in touch so that we can fix it. 

## Getting started
Package can be installed with pip  
```pip install swehockey_scraper```

In python, import module with  
```import swehockey.swehockey_scraper as swe```

See description of functions in package with  
```help(swe)```

Functions can be used together and input and output is linked. 


## Data structure

On the page for swehockey, there are two keys available, season_id and game_id. 

### Season ID 
For each season and league there is a schedule id. 
This is found in the URL, for example https://stats.swehockey.se/ScheduleAndResults/Schedule/6108 the season id is 6108. 

### Game ID 
Each game can be found with URL of structure https://stats.swehockey.se/Game/Events/252961
Here, the game id is the last part of the URL, e.g. 252961

### Functions

### getGames(season_id)
Input is a list of season ids. This returns a dataframe containing all games for the specific season together with results. 

### cleanGames(df_games)
Input is a list of the structure as returned from getGames(). 
This step cleans up the data and adds additional columns for further data processing. 

### getTeamData(df_games_clean)
Input is a list of the structure as returned from cleanGames(). 
This step make a dataframe on team level. It calculate season specific metrics for each team, Head-to-Head comparisons and table positions. 

### getGameData(df_games_clean)
Input is a list game_ids (for example can be extracted from the output from getGames).  
This function extracts game specific data like penaltys, goals, shot statistics.  


## Example Notebook 

See [this notebook](https://github.com/msjoelin/swehockey_scraper/blob/master/sample_workbook.ipynb) for examples of how to use the package, and in what order you can run the functions. 
