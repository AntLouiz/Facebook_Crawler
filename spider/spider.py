import requests
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from spider import settings
from bs4 import BeautifulSoup
from spider.utils import _get_reactions


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
        """
            This method make a GET http request using a
            requests session.
        """

        full_url = self.get_full_url(url)
        page_response = self.session.get(full_url)

        return page_response

    def login(self, email, password):
        logging.info("Trying to sign in on facebook.")

        self.session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        page = self.get('/home.php')
        parser = BeautifulSoup(page.content, 'html.parser')
        one_click_login_button = parser.find('a', href=re.compile('/login/save-device/cancel/'))
        home_page = parser.find('a', text='Página inicial')

        if not (home_page or one_click_login_button):
            logging.error("Failed to sign in.")
            self.is_logged_in = False
            return False

        logging.info("Login successful.")
        self.is_logged_in = True

    def crawl(self, *args, **kwargs):
        if not self.is_logged_in:
            logging.warn("Sign in problems, wrog credentials.")
            return False

        home_page = self.get('/home.php')
        parser = BeautifulSoup(home_page.content, 'html.parser')

        self.parser_perfil(parser)

        logging.info("Finished the crawl.")

    def parser_perfil(self, base_parser):
        """
            This parser search the user perfil page
            and go to the publications
        """

        perfil_url = base_parser.find('a', text='Perfil').get('href')

        perfil_page = self.get(perfil_url)
        parser = BeautifulSoup(perfil_page.content, 'html.parser')
        logging.info("Entering in the user perfil page.")

        self.parser_years_publications(parser)

    def parser_years_publications(self, base_parser):
        """
            This parser find all the publications years,
            for each year the parser go to the timeline
        """

        all_years_links = base_parser.find_all('a', {
            'href': re.compile('end_time')
        })

        max_threads = len(all_years_links)

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            for year_link in all_years_links:
                executor.submit(self.parser_year, year_link)

    def parser_year(self, year_url):
        year_link = year_url.get('href')
        logging.info("Scraping all publications of {0}".format(year_url.text))
        # enter in the year publications page
        page = self.get(year_link)
        parser = BeautifulSoup(page.content, 'html.parser')

        # get all publications of the year
        if parser:
            self.parser_timeline(parser)

    def parser_timeline(self, base_parser):
        """
            This parser scrap all publications of a year.
        """

        see_more_publications = True

        while see_more_publications:
            all_publications = base_parser.find_all(
                'a',
                text='História completa'
            )

            for pub in all_publications:
                # enter in the publication page detail
                pub_link = pub.get('href')
                page = self.get(pub_link)
                parser = BeautifulSoup(page.content, 'html.parser')

                try:
                    pub_date = parser.find('abbr').text

                except AttributeError:
                    pub_date = 'unknown'

                pub_data = {}

                # get the reactions link
                reactions = parser.find('a', {
                    'href': re.compile('/ufi/reaction/profile/browser/')
                })

                if reactions:
                    reactions_link = reactions.get('href')

                    pub_id = re.search(
                        r'ft_ent_identifier=(\d+)',
                        reactions_link
                    )

                    pub_data['_id'] = pub_id.group(1)
                    pub_data['date'] = pub_date
                    pub_data['reactions'] = {}

                    pub_database = self.collection.find_one(pub_data['_id'])
                    pub_data = _get_reactions(
                        self.session,
                        reactions_link,
                        pub_data
                    )

                    if pub_database:
                        if pub_database != pub_data:
                            self.collection.update(pub_database, pub_data)
                            logging.info(
                                "Publication updated: {0}".format(pub_data)
                            )
                    else:
                        logging.info(
                            "A new publication scrapped", pub_data
                        )

                if not pub_database:
                    self.collection.insert_one(pub_data).inserted_id
                    logging.info("A new publication scrapped.", pub_data)

            see_more_parser = base_parser.find('a', text='Mostrar mais')
            if see_more_parser:
                see_more_link = see_more_parser.get('href')
                page = self.get(see_more_link)
                base_parser = BeautifulSoup(page.content, 'html.parser')
            else:
                see_more_publications = False
