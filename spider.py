import requests
import re
from decouple import config
from pymongo import MongoClient
from bs4 import BeautifulSoup

#conn = MongoClient('localhost', 27017)


facebook_session = requests.session()

facebook_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
})

facebook_email = config('FACEBOOK_EMAIL', default=False) 
facebook_password = config('FACEBOOK_PASSWORD', default=False) 

reponse = facebook_session.get('https://m.facebook.com')

response = facebook_session.post('https://m.facebook.com/login.php', data={
    'email': facebook_email,
    'pass': facebook_password
}, allow_redirects=False)

home_page = facebook_session.get('https://m.facebook.com/home.php')

home_parser = BeautifulSoup(home_page.content, 'html.parser')

home_link = home_parser.find_all('a')

for link in home_link:
    if link.text == 'Perfil':
        print(link.get('href'))
        perfil_page = facebook_session.get("https://m.facebook.com{0}".format(link.get('href')))
        perfil_parser = BeautifulSoup(perfil_page.content, 'html.parser')
        break

years_links = perfil_parser.find_all('a', {'href':re.compile('yearSectionsYears')})

for year_link in years_links:
    print("--------->SCRAPPING ALL PUBLICATIONS OF {}".format(year_link.text))
    # enter in the year publications page
    year_page = facebook_session.get("https://m.facebook.com{0}".format(year_link.get('href')))
    year_parser = BeautifulSoup(year_page.content, 'html.parser')


    see_more = 1
    
    while see_more:
        pubs = year_parser.find_all('a', text='História completa') # get all page publications
        
        for pub in pubs:
            # enter in the publication page detail
            pub_page = facebook_session.get("https://m.facebook.com{0}".format(pub.get('href')))
            pub_parser = BeautifulSoup(pub_page.content, 'html.parser')
                
            print("--------->SCRAPED ONE PUBLICATION: {}".format(pub_parser.find('abbr').text))
            
            # get the reactions link
            reactions = pub_parser.find('a', {'href':re.compile('/ufi/reaction/profile/browser/')})

              
            if reactions:
                if not reactions.text:
                    reaction_type = "None"
                    reaction_user = "None"
                    print("{}:{}".format(reaction_user, reaction_type))

                reactions_link = reactions.get('href')
                
                # enter in the publication reactions list
                reactions_page = facebook_session.get("https://m.facebook.com{0}".format(reactions_link))
                reactions_parse = BeautifulSoup(reactions_page.content, 'html.parser')
                
                reactions_see_more = 1
                while reactions_see_more:                
                    for reaction in reactions_parse.find_all('li'):
                        # get the reaction type and the user that make this reaction
                        try:
                            reaction_type = reaction.img.next_element('img')[0].get('alt')
                            reaction_user = reaction.img.get('alt')
                            print("{}:{}".format(reaction_user, reaction_type))
                            
                        except:
                            pass
                    
                    reactions_see_more_parser = reactions_parse.find('a', text='Ver mais')
                    if reactions_see_more_parser:
                        reactions_link = reactions_see_more_parser.get('href')
                        reactions_page = facebook_session.get("https://m.facebook.com{0}".format(reactions_link))
                        reactions_parse = BeautifulSoup(reactions_page.content, 'html.parser')
                    else:
                        reactions_see_more = 0

                    #raise NotImplementedError

            see_more_parser = year_parser.find('a', text='Mostrar mais')
            if see_more_parser:
                see_more_link = see_more_parser.get('href')
                year_page = facebook_session.get("https://m.facebook.com{0}".format(see_more_link))
                year_parser = BeautifulSoup(year_page.content, 'html.parser')
            else:
                see_more = 0