from pymongo import MongoClient


conn = MongoClient('localhost', 27017)
conn.drop_database('test_mongo')

db = conn['test_mongo']



reaction = {
        'users':['Luiz Oliveira', 'Stephane Vale'],
        'type':'Curtir'
        }

timeline = db['timeline']

pubs = {
        'date':'19 de julho',
        'reactions':reaction
        }

pubs = timeline.insert_one(pubs).inserted_id

print(timeline.find_one())
