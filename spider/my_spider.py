import requests
import re
import logging
import settings
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup
from utils import _get_reactions
from decorators.auth import login_required

class My_Spider:
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
    )

    def __init__(self, collection):
        self.collection = collection
        self.start_url = 'https://m.facebook.com'
        self.used_urls = []
        self.logged = False
        self.session = requests.session()
        self.session.headers.update(settings.USER_AGENT)

    def _set_url(self, url):
        full_url = "{0}{1}".format(self.start_url, url)

        if full_url not in self.used_urls:
            self.used_urls.append(full_url)
        
        return full_url

    def get(self, url):
        full_url = self._set_url(url)
        page_response = self.session.get(full_url)

        return page_response

    def login(self, email, password):
        logging.info("TRYING TO SIGN IN ON FACEBOOK...")

        self.session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        page = self.get('/home.php')
        parser = BeautifulSoup(page.content, 'html.parser')

        if not parser.find('a', text='Página inicial'):
            logging.error("FAILED TO SIGN IN ON FACEBOOK.")
            self.logged = False
            return False

        logging.info("LOGIN SUCCESSFUL!")
        self.logged = True
        return True

    @login_required
    def crawl(self, *args):
        home_page = self.get('/home.php')
        parser = BeautifulSoup(home_page.content, 'html.parser')


        for i in self.parser_perfil(parser):
            print(i)
            next(i)

        logging.info("FINISHED THE FACEBOOK CRAWL .")
        return True

    @login_required
    def parser_perfil(self, base_parser):
        perfil_url = base_parser.find('a', text='Perfil').get('href')

        perfil_page = self.get(perfil_url)
        parser = BeautifulSoup(perfil_page.content, 'html.parser')
        logging.info("Entering in the user perfil page.")

        yield self.parser_all_publications(parser)

    @login_required
    def parser_all_publications(self, base_parser):
        all_years_links = base_parser.find_all('a', {'href':re.compile('yearSectionsYears')})

        for year_link in all_years_links:
            year_url = year_link.get('href')

            logging.info("SCRAPPING ALL PUBLICATIONS OF {0}".format(year_link.text))

            # enter in the year publications page
            page = self.get(year_url)
            parse = BeautifulSoup(page.content, 'html.parser')

            #get all publications of the year
            yield self.parser_publication_detail(parse)

    @login_required
    def parser_publication_detail(self, base_parser):
        see_more = 1
        
        while see_more:
            all_publications = base_parser.find_all('a', text='História completa') # get all page publications
            
            for pub in all_publications:
                # enter in the publication page detail
                pub_link = pub.get('href')
                page = self.get(pub_link)
                parser = BeautifulSoup(page.content, 'html.parser')
                pub_date = parser.find('abbr').text
                pub_data = {}
                    
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
                    page = self.get(see_more_link)
                    parser = BeautifulSoup(page.content, 'html.parser')
                else:
                    see_more = 0
        return True

if __name__ == '__main__':

    conn = MongoClient('localhost', 27017)

    db = conn['facebook_reactions_database']

    timeline = db['timeline']

    facebook_email = config('FACEBOOK_EMAIL', default=False) 
    facebook_password = config('FACEBOOK_PASSWORD', default=False)

    spider = My_Spider(timeline)
    spider.login(facebook_email, facebook_password)
    spider.crawl()
