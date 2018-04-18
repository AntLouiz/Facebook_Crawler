import requests
import re
import logging
from spider import settings
from bs4 import BeautifulSoup
from spider.utils import _get_reactions
from spider.decorators.auth import login_required


class FacebookSpider:
    """
        A spider to crawl on the Facebook
    """

    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
    )

    def __init__(self, collection):
        self.collection = collection
        self.start_url = 'https://m.facebook.com'
        self.is_logged_in = False
        self.session = requests.session()
        self.session.headers.update(settings.USER_AGENT)

    def get_full_url(self, url):
        full_url = "{0}{1}".format(self.start_url, url)
        
        return full_url

    def get(self, url):
        full_url = self.get_full_url(url)
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
            self.is_logged_in = False
            return False

        logging.info("LOGIN SUCCESSFUL!")
        self.is_logged_in = True
        return True

    @login_required
    def crawl(self, *args, **kwargs):
        home_page = self.get('/home.php')
        parser = BeautifulSoup(home_page.content, 'html.parser')

        self.parser_perfil(parser)

        logging.info("FINISHED THE FACEBOOK CRAWL .")
        return True

    @login_required
    def parser_perfil(self, base_parser):
        perfil_url = base_parser.find('a', text='Perfil').get('href')

        perfil_page = self.get(perfil_url)
        parser = BeautifulSoup(perfil_page.content, 'html.parser')
        logging.info("Entering in the user perfil page.")

        self.parser_years_publications(parser)

        return True

    @login_required
    def parser_years_publications(self, base_parser):
        all_years_links = base_parser.find_all('a', {'href':re.compile('yearSectionsYears')})

        for year_link in all_years_links:
            year_url = year_link.get('href')

            logging.info("SCRAPPING ALL PUBLICATIONS OF {0}".format(year_link.text))

            # enter in the year publications page
            page = self.get(year_url)
            parser = BeautifulSoup(page.content, 'html.parser')

            #get all publications of the year
            self.parser_timeline(parser)
            
        return True

    @login_required
    def parser_timeline(self, base_parser):
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

                    pub_id = re.search(
                        r'ft_ent_identifier=(\d+)',
                        reactions_link
                    )

                    pub_data['_id'] = pub_id.group(1)
                    pub_data['date'] = pub_date
                    pub_data['reactions'] = {}

                    pub_database = self.collection.find_one(pub_data['_id'])
                    pub_data = _get_reactions(self.session, reactions_link, pub_data)

                    if pub_database:  
                        if pub_database != pub_data:
                            self.collection.update(pub_database, pub_data)
                            logging.info("PUBLICATION UPDATED.\n{0}".format(pub_data))
                        else:
                            logging.info("THE PUBLICATION HAS ALREADY BEEN SCRAPED.")
                    else:
                        logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                
                if not pub_database:
                    self.collection.insert_one(pub_data).inserted_id
                    logging.info("PUBLICATION SCRAPED.\n{0}".format(pub_data))
                    print(pub_data)

            see_more_parser = base_parser.find('a', text='Mostrar mais')
            if see_more_parser:
                see_more_link = see_more_parser.get('href')
                page = self.get(see_more_link)
                base_parser = BeautifulSoup(page.content, 'html.parser')
            else:
                see_more = 0
        return True