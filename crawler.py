import time
import json
from decouple import config
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys


#date_regex = re.compile(r'^(\d+) de (\w+) às ((\d+):(\d+))$')
#time_regex = re.compile(r'^(\d+) (\w+)|Ontem às (\d+):(\d+)$')

class NoReactionException(Exception):
    pass

class PublicationExists(Exception):
    pass


conn = MongoClient('localhost', 27017)

db = conn['facebook_reaction']

timeline = db['timeline']


def start_crawl():
    #set the variables to be used on script
    email = config('FACEBOOK_EMAIL', default=False) 
    password = config('FACEBOOK_PASSWORD', default=False) 

    if not email:
        email = str(input("Insert your facebook email: "))
    if not password:
        password = str(input("Insert your facebook password: "))

    driver = webdriver.Firefox()

    #connect with facebook
    driver.get("http://m.facebook.com/")
    print("Connected with facebook")
    
    #get the email field
    email_field = driver.find_element_by_name('email')
    email_field.clear()

    #insert the email
    email_field.send_keys(email)
    print("Email inserted")

    #get the password field
    pass_field = driver.find_element_by_name('pass') 
    pass_field.clear()

    #insert the password
    pass_field.send_keys(password)
    print("Password inserted")

    #get the login button
    login_button = driver.find_element_by_name('login')

    #click on login button
    login_button.click()
    print("Button login clicked.")
    time.sleep(2)

    ok_button = driver.find_element_by_xpath('//input[@value="OK"]').click()
    print("Ok pressed in Entry on touch page.")

    #send to user perfil
    perfil = driver.find_element_by_link_text('Perfil').click()
    print("Entry on Perfil.")

    #select the year to be catch all publications
    year = driver.find_element_by_link_text('2012').click()


    try:
        #the "See More" link
        more = driver.find_element_by_link_text('Mostrar mais')
    except:
        more = 1


    #while the "See More" is on the page catch all publications
    while more:
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        #get all publications
        publications = soup.find_all('a', text='Curtir')

        #get the main window
        main_window = driver.current_window_handle

        for publication in publications:

            try:
                #get the publication date
                pub_date = driver.find_element_by_xpath('//abbr[1]').text

            except:
                continue

            #make a publication dict
            pub = {}

            try:
                #get the link of publication reactions 
                reaction_link = publication.find_previous_sibling('a')

                if reaction_link:
                    reaction_link = reaction_link.get('href')
                else:
                    raise NoReactionException

                pub['_id'] = reaction_link
                pub['reaction_link'] = reaction_link
                pub['date'] = pub_date
                pub['reactions'] = {}

                if timeline.find_one(pub['_id']):
                    raise PublicationExists

                #got to the publication detail
                driver.execute_script('window.open("{0}");'.format(reaction_link))
                time.sleep(1)

                #switch to the new open tab
                driver.switch_to_window(driver.window_handles[1])
                time.sleep(1)

         
                #click on the link of list of reactions
                driver.find_element_by_xpath(
                    '//div[@id="add_comment_switcher_placeholder"]/following-sibling::div/a'
                ).click()

                while True:
                    time.sleep(1)
                    reactions = BeautifulSoup(driver.page_source, 'html.parser').find_all('li')

                    try:
                        see_more = driver.find_element_by_link_text('Ver mais')
                        reactions = reactions[:len(reactions)-1]

                    except:
                        see_more = 0

                    for reaction in reactions:
                        reaction = reaction.find_all('img')[:2]
                        user_name = reaction[0].get('alt')
                        user_reaction = reaction[1].get('alt')

                        try:
                            pub['reactions'][user_reaction].append(user_name)

                        except KeyError:
                            pub['reactions'][user_reaction] = []
                            pub['reactions'][user_reaction].append(user_name)

                    if see_more:
                        see_more.click()

                    else:
                        break

                driver.close()
                driver.switch_to_window(main_window)
                timeline.insert_one(pub)

            except PublicationExists:
                #if the publication does have any reactions
                print("---------> THE PUBLICATION IS ALREADY IN DATABASE.")

            except NoReactionException:
                pub['reactions'] = {'0':'Ninguem Curtiu'}
                timeline.insert_one(pub)
                print(
                    "---------> A NEW PUBLICATION SCRAPED: \n{0}".format(
                        pub
                ))

            else:
                print(
                    "---------> A NEW PUBLICATION SCRAPED: \n{0}".format(
                        pub
                ))


        try:
            more = driver.find_element_by_link_text('Mostrar mais')
            more.click()

        except:
            more = 0

    driver.close()

if __name__ == '__main__':
    start_crawl()
