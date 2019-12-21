import pandas as pd
import sqlite3
import urllib.request
import urllib.parse
import requests
from pandas.io.json import json_normalize
from pathlib import Path
from utils.connections import keys


#DB Connection
conn = sqlite3.connect(Path('./data/keys.db'))
key = keys()


class USDA():

    def __init__(self,state,crop):
        self.state = state
        self.crop = crop
   


    key = key['value'][0]

    #USDA API
    def crop_survey(self,year,key=key):
        
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
                        'year':year,
                        'format':'JSON'}

    
        #Combine and encode
        querystring = urllib.parse.urlencode(query_params)
        url = get_url + querystring
        
        print(f'Connecting to {get_url}')

        #API Response
        try:
            resp = requests.get(url).json()
            print('Preparing dataframe')
            data = json_normalize(resp['data'])

        
            df = self.prep_survey(data).drop_duplicates(subset='countycd',keep='first')
            print('Success!')
            
        except requests.exceptions.RequestException as e:
            print(e)

        return df


    def loss_hist(self):

        data = pd.read_csv(Path('./data/total_loss_hist.csv'))
        df = data[(data.statecd==self.state) & (data.crop==self.crop)]

        return df

    def weather_hist(self):

        data = pd.read_csv(Path('./data/weather_hist.csv'))
        df = data[data.statecd==self.state]
        return df

    def prep_survey(self,df):

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
        data['AREA HARVESTED'] = data['AREA HARVESTED'].replace(regex=True,to_replace=r'\D',value=r'').astype('int')
        data['AREA PLANTED'] = data['AREA PLANTED'].replace(regex=True,to_replace=r'\D',value=r'').astype('int')
        data['PRODUCTION'] = data['PRODUCTION'].replace(regex=True,to_replace=r'\D',value=r'').astype('int')

        final = data.rename(columns={'county_code':'countycd','county_name':'countyname',
                                'state_ansi':'statenbr','state_alpha':'statecd',
                                'commodity_desc':'crop','AREA HARVESTED':'areaharvested',
                                'AREA PLANTED':'areaplanted','PRODUCTION':'production','YIELD':'yield'})
        
        return final


    def features(self):

        years = [2014,2015,2016,2017,2018]
        sur_list = []

        for year in range(len(years)):
            sur = self.crop_survey(years[year])
            sur_list.append(sur)


        loss = self.loss_hist()
        wthr = self.weather_hist()
        sur = pd.concat(sur_list)

        df = pd.merge(sur,loss[['countycd','year','totalacreloss',
                                    'total_events','imdemnityamt']],
                                on=['countycd','year'],
                                how='left')

        final = pd.merge(df,wthr[['statecd','year','percipavg', 'droughtavg', 
                                'tempavg', 'shortdroughtavg','mintempavg',
                                 'maxtempavg']],
                             on = ['statecd','year'],how='left')
        
        return final



