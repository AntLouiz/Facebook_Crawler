import time
import json
from decouple import config
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys


def start_crawl():
    #set the variables to be used on script
    email = config('FACEBOOK_EMAIL', default=False) 
    password = config('FACEBOOK_PASSWORD', default=False) 

    if not email:
        email = str(input("Insert your facebook email: "))
    if not password:
        password = str(input("Insert your facebook password: "))

    driver = webdriver.Firefox()
    data = {} # set a dict to store all publications reactions data

    #connect with facebook
    driver.get("http://m.facebook.com/")
    print("Connected with facebook")
    time.sleep(2)

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
    time.sleep(2)

    #send to user perfil
    perfil = driver.find_element_by_link_text('Perfil').click()
    print("Entry on Perfil.")
    time.sleep(2)

    #select the year to be catch all publications
    year = driver.find_element_by_link_text('2017').click()
    time.sleep(2)

    #the "See More" link
    more = driver.find_element_by_link_text('Mostrar mais')


    #while the "See More" is on the page catch all publications
    while more:
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        #get all publications
        publications = soup.find_all('a', text='Curtir')

        #get the main window
        main_window = driver.current_window_handle

        for publication in publications:

            #get the publication date
            pub_date = driver.find_element_by_xpath('//abbr[1]').text

            #make a publication dict
            data[pub_date] = {}

            try:
                #get the link of publication reactions 
                reaction_link = publication.find_previous_sibling('a').get('href')

                #got to the publication detail
                time.sleep(3)
                driver.execute_script('window.open("{0}");'.format(reaction_link))
                time.sleep(2)

                #switch to the new open tab
                driver.switch_to_window(driver.window_handles[1])
                time.sleep(2)

         
                #click on the link of list of reactions
                driver.find_element_by_xpath(
                    '//div[@id="add_comment_switcher_placeholder"]/following-sibling::div/a'
                ).click()

                while True:
                    time.sleep(4)
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
                            data[pub_date][user_reaction].append(user_name)

                        except KeyError:
                            data[pub_date][user_reaction] = []
                            data[pub_date][user_reaction].append(user_name)

                    if see_more:
                        see_more.click()
                        time.sleep(4)

                    else:
                        break
                        
                time.sleep(3)
                driver.close()
                driver.switch_to_window(main_window)

            except:
                #if the publication does have any reactions
                data[pub_date] = 'Ninguem curtiu'

            print(data[pub_date])

        try:
            more = driver.find_element_by_link_text('Mostrar mais')
            more.click()
            time.sleep(2)

        except:
            more = 0

    driver.close()

    return data

if __name__ == '__main__':
    data = start_crawl()

    with open('facebook_data.json', 'w') as fb_data:
        json.dump(data, fb_data)