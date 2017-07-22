import requests
import re
import logging
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup

def get_publications(session, collection, parser):
        see_more = 1
        
        while see_more:
            all_publications = parser.find_all('a', text='História completa') # get all page publications
            
            for pub in all_publications:
                # enter in the publication page detail
                page = session.get("https://m.facebook.com{0}".format(pub.get('href')))
                parser = BeautifulSoup(page.content, 'html.parser')
                pub_data = {}

                pub_date = parser.find('abbr').text
                    
                # get the reactions link
                reactions = parser.find('a', {'href':re.compile('/ufi/reaction/profile/browser/')})

                  
                if reactions:
                    if not reactions.text:
                        reaction_type = "None"
                        reaction_user = "None"

                    reactions_link = reactions.get('href')

                    pub_data['_id'] = reactions_link
                    pub_data['date'] = pub_date
                    pub_data['reactions'] = {}

                    pub_db = collection.find_one(pub_data['_id'])
                    pub_data = get_reactions(session, reactions_link, pub_data)

                    if pub_db:  
                        if pub_db != pub_data:
                            collection.update(pub_db, pub_data)
                            logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                        else:
                            logging.info("THE PUBLICATION HAS ALREADY BEEN SCRAPED.")
                    else:
                        logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                
                if not pub_db:
                    collection.insert_one(pub_data).inserted_id
                    logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))

                see_more_parser = parser.find('a', text='Mostrar mais')
                if see_more_parser:
                    see_more_link = see_more_parser.get('href')
                    year_page = session.get("https://m.facebook.com{0}".format(see_more_link))
                    parser = BeautifulSoup(year_page.content, 'html.parser')
                else:
                    see_more = 0
                    
        logging.info("FINISHED THE FACEBOOK CRAWL .")
        return 1

def get_reactions(session, reactions_link, publication):
    # enter in the publication reactions list
    page = session.get("https://m.facebook.com{0}".format(reactions_link))
    parser = BeautifulSoup(page.content, 'html.parser')
                    
    reactions_see_more = 1
    while reactions_see_more:                
        for reaction in parser.find_all('li'):
            # get the reaction type and the user that make this reaction
            try:
                reaction_type = reaction.img.next_element('img')[0].get('alt')
                reaction_user = reaction.img.get('alt')
                try:
                    publication['reactions'][reaction_type].append(reaction_user)

                except KeyError:
                    publication['reactions'][reaction_type] = []
                    publication['reactions'][reaction_type].append(reaction_user)
                                
            except:
                pass
                        
        reactions_see_more_parser = parser.find('a', text='Ver mais')
        if reactions_see_more_parser:
            reactions_link = reactions_see_more_parser.get('href')
            page = session.get("https://m.facebook.com{0}".format(reactions_link))
            parser = BeautifulSoup(page.content, 'html.parser')
        else:
            reactions_see_more = 0

    return publication