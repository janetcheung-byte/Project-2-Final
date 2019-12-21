import pandas as pd
import sqlite3
import urllib.request
import urllib.parse
import requests
from pandas.io.json import json_normalize
from pathlib import Path
from connections import keys


#DB Connection
conn = sqlite3.connect(Path('./data/keys.db'))
key = keys()


class USDA():

    def __init__(self,state,crop,year):
        self.state = state
        self.crop = crop
        self.year = year

    #USDA API
    def crop_stat(self,key=key):
        
        get_url = 'http://quickstats.nass.usda.gov/api/api_GET/?'

        #Update query with key 
        print('Passing key to query params..')
        query_params = {'key':key,
                        'source_desc':'SURVEY',
                        'sector_desc': 'CROPS',
                        'group':'FIELD CROPS',
                        'commodity_desc':self.crop,
                        'agg_level_desc':'COUNTY',
                        'state_alpha':self.state,
                        'year':self.year,
                        'format':'JSON'}

    
        #Combine and encode
        querystring = urllib.parse.urlencode(query_params)
        url = get_url + querystring
        
        print(f'Connecting to {get_url}')

        #API Response
        try:
            resp = requests.get(url).json()
            print('Preparing dataframe')
            df = json_normalize(resp['data'])

        
            data = self.prep_stat_data(df).drop_duplicates(subset='county_code',keep='first')
            print('Success!')
            
        except requests.exceptions.RequestException as e:
            print(e)

        return data


    def loss_hist(self):

        data = pd.read_csv(Path('./data/total_loss_hist.csv'))
        df = data[(data.statecd==self.state) & (data.crop==self.crop)]

        return df


    def prep_stat_data(self,df):

        cols = ['county_code','county_name','state_ansi','state_name',
            'state_alpha','commodity_desc','state_fips_code',
            'year']
        

        #Pivot the dataframe
        df1 = df.pivot(index=cols[0],columns='statisticcat_desc',values='Value')

        #Create new df with only cols.
        df2 = df.filter(cols, axis=1)

        #Create final df
        data = pd.merge(df2,df1,how='inner',on='county_code')
        
        #Convert values to int
        data['county_code'] = data['county_code'].astype('int')

        data.rename(columns={'county_code':'countycd','county_name':'countyname',
                                'state_ansi':'statenbr','state_alpha':'statecd',
                                'commodity_desc':'crop'})
        
        return data




