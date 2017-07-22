import requests
import re
import logging
import settings
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup
from utils import _get_publications

def check_login(method):

    def check(self, *args):
        if self.logged:
            return method(self, *args)
        else:
            logging.warn("YOU MUST SIGN ON FACEBOOK.")

    return check

class My_spider:
    logging.getLogger().setLevel(logging.INFO)

    def __init__(self, collection):
        self.collection = collection
        self.url = 'https://m.facebook.com'
        self.session = requests.session()
        self.session.headers.update(settings.USER_AGENT)
        self.logged = False

    def login(self, email, password):
        logging.info("TRYING TO SIGN IN ON FACEBOOK...")

        self.session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        page = self.session.get('https://m.facebook.com/home.php')
        parser = BeautifulSoup(page.content, 'html.parser')

        if not parser.find('a', text='Página inicial'):
            logging.error("FAILED TO SIGN IN ON FACEBOOK.")
            self.logged = False
            return False

        logging.info("LOGIN SUCCESSFUL!")
        self.logged = True
        return True

    @check_login
    def crawl(self, *args):
        home_page = self.session.get('https://m.facebook.com/home.php')
        parser = BeautifulSoup(home_page.content, 'html.parser')

        return self.parser_perfil(parser)

    @check_login
    def parser_perfil(self, base_parser):
        perfil_link = base_parser.find('a', text='Perfil')

        perfil_page = self.session.get("https://m.facebook.com{0}".format(perfil_link.get('href')))
        parser = BeautifulSoup(perfil_page.content, 'html.parser')
        logging.info("Entering in the user perfil page.")

        return self.parser_all_publications(parser)

    @check_login
    def parser_all_publications(self, base_parser):
        all_years_links = base_parser.find_all('a', {'href':re.compile('yearSectionsYears')})

        for year_link in all_years_links:
            logging.info("SCRAPPING ALL PUBLICATIONS OF {0}".format(year_link.text))

            # enter in the year publications page
            page = self.session.get("https://m.facebook.com{0}".format(year_link.get('href')))
            parse = BeautifulSoup(page.content, 'html.parser')

            #get all publications of the year
            return self.parser_publication_detail(parse)

    @check_login
    def parser_publication_detail(self, base_parser):
        see_more = 1
        
        while see_more:
            all_publications = base_parser.find_all('a', text='História completa') # get all page publications
            
            for pub in all_publications:
                # enter in the publication page detail
                page = self.session.get("https://m.facebook.com{0}".format(pub.get('href')))
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

                    pub_db = self.collection.find_one(pub_data['_id'])
                    pub_data = _get_reactions(self.session, reactions_link, pub_data)

                    if pub_db:  
                        if pub_db != pub_data:
                            self.collection.update(pub_db, pub_data)
                            logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                        else:
                            logging.info("THE PUBLICATION HAS ALREADY BEEN SCRAPED.")
                    else:
                        logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                
                if not pub_db:
                    self.collection.insert_one(pub_data).inserted_id
                    logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))

                see_more_parser = base_parser.find('a', text='Mostrar mais')
                if see_more_parser:
                    see_more_link = see_more_parser.get('href')
                    page = self.session.get("https://m.facebook.com{0}".format(see_more_link))
                    parser = BeautifulSoup(page.content, 'html.parser')
                else:
                    see_more = 0

        logging.info("FINISHED THE FACEBOOK CRAWL .")
        return 1

if __name__ == '__main__':

    conn = MongoClient('localhost', 27017)

    db = conn['facebook_reactions_database']

    timeline = db['timeline']

    spider = My_spider(timeline)
    spider.login('luizrodrigo46@hotmail.com', 'luiz05012015')
    spider.crawl()