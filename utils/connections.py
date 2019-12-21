import pandas as pd
import sqlite3
from pathlib import Path


def keys(name=None):
    
    print('Connecting to keys.db')
    conn = sqlite3.connect(Path('./data/keys.db'))
    
    if bool(name)==True:
    
        key = pd.read_sql_query(f"""select value from api_keys where name=:name""",conn,params={'name':name})
        print(f'Returning the key for {name}')
        conn.close()
        print('Connection to keys.db closed')

        
    else:
        
        key = pd.read_sql_query(f"""select * from api_keys""",conn,params={'name':name})
        print('Retrieved Keys')
        
        conn.close()
        print('Connection to keys.db closed')

    return key

