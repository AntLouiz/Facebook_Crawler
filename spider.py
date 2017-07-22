import requests
import re
import logging
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup
from utils import get_publications, get_reactions


def start_craw(session, collection, email, password):
    logging.getLogger().setLevel(logging.INFO)

    reponse = session.get('https://m.facebook.com')
    logging.info("Connected with Facebook")

    response = session.post('https://m.facebook.com/login.php', data={
        'email': facebook_email,
        'pass': facebook_password
    }, allow_redirects=False)

    logging.debug("User logged in.")

    home_page = session.get('https://m.facebook.com/home.php')

    home_parser = BeautifulSoup(home_page.content, 'html.parser')

    home_link = home_parser.find_all('a')

    for link in home_link:
        if link.text == 'Perfil':
            perfil_page = session.get("https://m.facebook.com{0}".format(link.get('href')))
            perfil_parser = BeautifulSoup(perfil_page.content, 'html.parser')

            logging.info("Entering in the user perfil page.")
            break

    years_links = perfil_parser.find_all('a', {'href':re.compile('yearSectionsYears')})

    for year_link in years_links:

        logging.info("SCRAPPING ALL PUBLICATIONS OF {0}".format(year_link.text))
        # enter in the year publications page
        year_page = session.get("https://m.facebook.com{0}".format(year_link.get('href')))
        year_parser = BeautifulSoup(year_page.content, 'html.parser')

        get_publications(session, collection, year_parser)

if __name__ == '__main__':
    facebook_session = requests.session()

    facebook_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    facebook_email = config('FACEBOOK_EMAIL', default=False) 
    facebook_password = config('FACEBOOK_PASSWORD', default=False)

    conn = MongoClient('localhost', 27017)

    db = conn['facebook_reactions_database']

    timeline = db['timeline']

    start_craw(
        facebook_session,
        timeline,
        facebook_email,
        facebook_password,
    )
