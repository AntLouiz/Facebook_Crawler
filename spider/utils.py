from bs4 import BeautifulSoup


def _get_reactions(session, reactions_link, publication):
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
            page = session.get(
                "https://m.facebook.com{0}".format(reactions_link)
            )
            parser = BeautifulSoup(page.content, 'html.parser')
        else:
            reactions_see_more = 0

    return publication
