import pandas as pd
from pybaseball import statcast
import pickle
import numpy as np
from pybaseball import chadwick_register
import logging
from datetime import date
import xgboost

def get_data():
    # get yesterday's data
    data = statcast()

    # get saved data
    from_csv = pd.read_csv('data/shadow_zone_data_2022.csv')

    # get player teams
    player_teams = pd.read_csv('data/player_team_ids.csv')

    # load model
    cl = pickle.load(open('scoe_model.pkl', 'rb'))

    # load players data
    players = chadwick_register()
    players['full_name'] = players['name_first'] + ' ' + players['name_last']

    cols_to_use = ['sz_top', 'sz_bot', 'pitcher', 'batter', 'fielder_2', 'pitch_name', 'balls', 'strikes', 'release_pos_x', 'release_pos_z', 'release_speed', 'pfx_x', 'pfx_z', 'plate_x', 'plate_z', 'outs_when_up', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az', 'effective_speed', 'release_spin_rate', 'release_extension', 'release_pos_y', 'zone', 'p_throws', 'stand', 'pitch_number', 'spin_axis', 'called_strike']
    # clean the new data
    data = data.loc[data['description'].isin(['called_strike', 'ball'])]
    data = data.loc[((data['plate_z'] <= data['sz_top']+(1/3)) & (data['plate_z'] >= data['sz_top']-(1/3)) & (data['plate_x'] >= -1.108) & (data['plate_x'] <= 1.108)) | ((data['plate_z'] <= data['sz_bot']+(1/3)) & (data['plate_z'] >= data['sz_bot']-(1/3)) & (data['plate_x'] >= -1.108) & (data['plate_x'] <= 1.108)) | ((data['plate_x'] >= -1.108) & (data['plate_x'] <= -0.558) & (data['plate_z'] <= data['sz_top']-(1/3)) & (data['plate_z'] >= data['sz_bot']+(1/3))) | ((data['plate_x'] <= 1.108) & (data['plate_x'] >= 0.558) & (data['plate_z'] <= data['sz_top']-(1/3)) & (data['plate_z'] >= data['sz_bot']+(1/3)))] 
    data['called_strike'] = np.where(data['description'] == "called_strike", 1, 0)
    data = data[cols_to_use]
    data = data.dropna()
    data = data.merge(players[['key_mlbam', 'full_name']], left_on='fielder_2', right_on='key_mlbam')
    data = data.drop(['key_mlbam'], 1)
    data = data.rename(columns={'full_name' : 'catcher_name'})
    data = data.merge(players[['key_mlbam', 'full_name']], left_on='pitcher', right_on='key_mlbam')
    data = data.drop(['key_mlbam'], 1)
    data = data.rename(columns={'full_name' : 'pitcher_name'})
    data = data.merge(players[['key_mlbam', 'full_name']], left_on='batter', right_on='key_mlbam')
    data = data.drop(['key_mlbam'], 1)
    data = data.rename(columns={'full_name' : 'batter_name'})
    data = data.merge(player_teams, left_on='fielder_2', right_on='player_id')
    data = data.drop(columns=['player_id'], axis=1)
    data = data.rename(columns={'team_name' : 'catcher_team'})
    data = data.merge(player_teams, left_on='pitcher', right_on='player_id')
    data = data.drop(columns=['player_id'], axis=1)
    data = data.rename(columns={'team_name' : 'pitcher_team'})
    data = data.merge(player_teams, left_on='batter', right_on='player_id')
    data = data.drop(columns=['player_id'], axis=1)
    data = data.rename(columns={'team_name' : 'batter_team'})

    X_2022 = data.drop(['pitcher', 'batter', 'fielder_2', 'called_strike', 'sz_top', 'sz_bot', 'catcher_name', 'pitcher_name', 'batter_name'], 1)
    X_2022 = pd.get_dummies(X_2022, columns=['pitch_name', 'balls', 'strikes', 'outs_when_up', 'zone', 'p_throws', 'stand'])
    X_2022.to_csv('data/X_2022.csv', index=False)
    X_2022 = pd.read_csv('data/X_2022.csv')

    diff = 56 - len(X_2022.columns.tolist())

    if diff != 0:
        for i in range(0, diff):
            col_name = 'add_' + str(i)
            X_2022[col_name] = 0

    # run through model
    y_pred_2022 = cl.predict_proba(X_2022)
    y_pred_2022 = y_pred_2022.tolist()
    y_pred_2022 = [l[1] for l in y_pred_2022]
    data['strike_proba'] = y_pred_2022

    # update csv file
    data_out = pd.concat([from_csv, data], axis=1, ignore_index=True)
    data_out.to_csv('data/shadow_zone_data_2022.csv', index=False)    

    logging.info('Yay! - csv data updated ' + str(date.today()))


if __name__ == "__main__":
    get_data()
