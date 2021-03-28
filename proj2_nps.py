#################################
##### Name: Greg Nickel  ########
##### Uniqname: gnickel  ########
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_DICT = {} #Storage location for querried data
'''
The program includes a user-interface to query the National Parks website. After
exploring the National Parks, users can look for local business (up to ten) that are
nearby the National Site (within 10 miles).
The structure of the program consist of an outer(main) loop, an inner loop and a
few smaller loops that verify user entries.
The outer/main loop takes user entries, tries to convert that into a querry about
a state or territory.
The inner loops takes the state data, returns the list of national sites, and gives
the option to look for nearby businesses.
When users type "back" when looking at National Sites, it will return them to
the main loop and ask for a new state.
When users type 'back' when looking at Nearby Businesses, it will return them to
the National Sites list for the given state.
All web/api requests make use of CACHE_DICT which stores response information.
'''

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        '''
        Returns formated string representation of a National site
        The format is <name> (<category>): <address> <zip> .
        Example: Isle Royale (National Park): Houghton, MI 49931

            Parameters
        ----------
        none

        Returns
        -------
        string

        '''
        return (f"{self.name} ({self.category}): {self.address} {self.zipcode}")

    def to_dict(self):
        '''
        Returns a dictionary representation of an National Site object with each
        key/value pair being an instance variable and it's value.
            Parameters
        ----------
        none

        Returns
        -------
        dict

        '''
        rep_dict = {
        "category" : self.category,
        "name": self.name,
        "address": self.address,
        "zipcode": self.zipcode,
        "phone": self.phone
        }
        return rep_dict

    def get_zip(self):
        '''
        Returns the zipcode/postalcode for a National Sites Object
        ----------
        none

        Returns
        -------
        String

        '''
        return self.zipcode

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    BASE_URL = "https://www.nps.gov"
    abbreviation_dict = {}
    response = requests.get("https://www.nps.gov/index.htm")
    data_soup = BeautifulSoup(response.text, 'html.parser')
    state_list_div = data_soup.find('div', class_="SearchBar-keywordSearch input-group input-group-lg")
    state_list = state_list_div.find_all('a')
    for state in state_list:
        name = state.text.strip().lower()
        url = BASE_URL + state['href']
        abbreviation_dict[name] = url
    return abbreviation_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
        Also stores information in cache

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''
    try:
        site_info = CACHE_DICT[site_url]
        category = site_info["category"]
        name = site_info["name"]
        address = site_info['address']
        zipcode = site_info["zipcode"]
        phone = site_info["phone"]
        print("Using Cache")
    except KeyError:
        print("Fetching")
        response = requests.get(site_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('a', class_="Hero-title").text.strip()
        category = soup.find('span', class_="Hero-designation").text.strip()
        if soup.find('span', class_='postal-code') == None:
            zipcode = "00000" #Default value
        else:
            zipcode = soup.find('span', class_='postal-code').text.strip()
        if soup.find('span', class_='region') == None:
            state = "Not listed"
        else:
            state = soup.find('span', class_='region').text.strip()
        if soup.find('span', itemprop="addressLocality") == None:
            city = "No city"
        else:
            city = soup.find('span', itemprop="addressLocality").text.strip()
        address = f"{city}, {state}"
        phone = soup.find('span', class_='tel').text.strip()

    nat_site_object = NationalSite(category, name, address, zipcode, phone)
    construct_cache(site_url,nat_site_object.to_dict())

    return nat_site_object

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''
    sites_url_list = []

    #Check Cache for data or Fetch New Data
    try:
        sites_url_list = CACHE_DICT[state_url]
        print("Using Cache")
    except KeyError:
        print("Fetching")
        response = requests.get(state_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        sites_list = soup.find_all('h3')

        for site in sites_list:
            link = site.find('a')
            if link is not None:
                url = "https://www.nps.gov" + link['href']
                sites_url_list.append(url)
        construct_cache(state_url,sites_url_list)

    national_sites_list = []
    for url in sites_url_list:
        site_object = get_site_instance(url)
        national_sites_list.append(site_object)

    return national_sites_list

def get_nearby_places(site_object):
    '''
    Check Cache for previously returned results.
    Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    zip = site_object.get_zip()

    if zip == "00000": #In instantiated, 00000 was the default value
        print("For the National Site you inqired about, there maybe an issure with the address as recorded.")

    try:
        data = CACHE_DICT[zip]
        print("Using Cache")
    except KeyError:
        print("Fetching")
        BASE = "http://www.mapquestapi.com/search/v2/radius"
        key = secrets.API_KEY
        params = {
            "key":key,
            "origin":zip,
            "maxMatches" : 10,
            "radius" : 10,
            "ambiguities": "ignore",
            "outFormat": "json"
        }
        response = requests.get(BASE,params)
        data = json.loads(response.text)
        CACHE_DICT[zip]=data #Update Cache
    return data


#Additional Functions
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open('cache.json', 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open('cache.json',"w")
    fw.write(dumped_json_cache)
    fw.close()

def construct_cache(item_url,data_set,storage=CACHE_DICT):
    ''' constructs a key based on the National Parks URL and stores instance 
    variables as a nested dictionary for National Sites or Site URLS for a given state
    Parameters

    ----------
    item_url: string
        The URL for the API endpoint
    data_set: dict or list
        Either Dict Representation of a national site
        or
        List of site urls for a given state

    Returns
    -------
    None
    '''
    CACHE_DICT[item_url] = data_set

def state_abbreviations_maker(abbreviation, dictionary):
    '''
    Given the dictionary of states and URLs, this will return the postal code
    abbreviation used by the National Sties website. Or return a "no" string

    Parameters
    ----------
    abbreviation: string
        Possible state abbreviation
    dictionary: dict
        dictionary of urls

    Returns
    -------
        dictionary of abberviations and state names
    '''
    for key, val in dictionary.items():
         if abbreviation == val[-12:-10]:
             return key
    return "no"

def nearby_places_to_string(data):
    '''Given a converted MapQuest API response, returns a list of formatted strings
    of the form '- <location name> (<category>): <street address>, <city>'
    Fields that are either empty or nont denoted are given the value 'no <field>'

    Parameters
    ----------
    data: (dict)
        return from get_nearby_places()

    Returns
    -------
    formated_responses: list
        list of formatted responses
    '''
    formated_responses = []
    list_of_responses = data["searchResults"]
    for x in list_of_responses:
        try:
            name = x['name']
            if name == "":
                name = "no Name"
        except KeyError:
            name = "No Name" #Unlikely, but defensive progamming
        try:
            category = x['fields']['group_sic_code_name_ext']
            if category == "":
                category = "no category"
        except KeyError:
            category = 'no category'
        try:
            address = x['fields']['address']
            if address == "":
                address = 'no address'
        except KeyError:
            address = "no address"
        try:
            city = x['fields']['city']
            if city == "":
                city = 'no city'
        except KeyError:
            city = "no city"
        statement = f"- {name} ({category}): {address}, {city}"
        formated_responses.append(statement)
    return formated_responses



if __name__ == "__main__":
    #initial variables
    CACHE_DICT= open_cache()
    state_url_dict = build_state_url_dict()
    print("Welcome the the National Sites Finder!")

    #Begin user-interface
    state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: ')

    main = True #Main loop for picking states/Control Variable
    while main == True:
        state = state.lower() #Make search/state lower case

        #Gives users another options for lists of states, including examples of Territory/Non-states
        if state == 'help':
            key = list(state_url_dict.keys())
            print(f"Examples of states include: {key[0].title()}, {key[1].title()}, {key[2].title()}, {key[3].title()} and many more...")
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit: ')
            continue

        if state in ("exit","quit","exi"): #defensive programming
            break

        #Check and see if user entered an abbreviation rather than a state name
        # (i.e. typing in MI would prompt the user if they meant "Michigan") Not required, but helpful
        abbrev = state_abbreviations_maker(state,state_url_dict)
        if abbrev in state_url_dict.keys():
            check = input(f'You typed "{state.upper()}"", but did you mean "{abbrev.title()}"? Type "Yes" or "No" ')
            if check.lower() in ['y', 'ye', 'yes']:
                state = abbrev

        #It appears user has not entered a valid state, prompt again
        if state not in state_url_dict.keys():
            print("That doesn't appear to be a state. Please try again.")
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: ')
            continue

        #Response appears to be a state, present list of state National Sites
        inner=True #inner loop for looking at state results and nearby places/control variable

        if state in state_url_dict.keys():
            while inner == True:
                state_url = state_url_dict[state]
                list_of_sites = get_sites_for_state(state_url)
                #Print Header
                print(70*"-")
                if state == "ohio":
                    print("Here are the National Sites in the state of Ohio.") #Not required
                elif state in ['american samoa', 'guam', 'virgin islands', 'northern mariana islands']:
                    if state in ['virgin islands', 'northern mariana islands']:
                        print(f"Here are the National Sites in the beautiful territory of the {state.title()}.") #Puts property article in front of territory name
                    else:
                        print(f"Here are the National Sites in the beautiful territory of {state.title()}.")
                elif state == 'district of columbia':
                    print(f"Here are the National Sites in the nation's capitol.")
                else:
                    print(f"Here are the National Sites in the lovely state of {state.title()}")
                print(70*"-")

                #Print List of National Sites
                counter = 1
                for site in list_of_sites:
                    print(f"[{counter}] {site.info()}")
                    counter += 1

                #Prompt user for navigation of results
                nearby_number = input('Choose a number for a more detailed search or "back" for a new state or "exit" to quit: ')
                nearby_navigator = "No" #Defines variable that might be skipped by user if they choose not to look at nearby businesses

                #The nearby_number needs to be a number or back or exit. The program will loop and prompt until it gets a valid response
                complex_boolean = (nearby_number.isnumeric() and int(nearby_number) < counter) or nearby_number.lower() in ['back','exit']
                while not complex_boolean:
                    print("That number is outside the range of possibilities. Try again")
                    nearby_number = input('Choose a valid number for a more detailed search, "back" for a new state or "exit" to quit ')
                    if nearby_number.isnumeric():
                        if int(nearby_number) >= counter:
                            complex_boolean = False #Number is too large, still fails to be valid
                            print("Your number is too large")
                        else:
                            complex_boolean = True #Number is valid, you may proceed
                    if nearby_number.lower() in ['back','exit']:
                        break #Break verifictation loop

                # Given a valid number, either go back, exit or print nearby results
                if nearby_number.lower() == 'back':
                    break #break inner loop, pick new state
                elif nearby_number.lower() == 'exit':
                    nearby_navigator = 'exit' #Skips prompt for new state at end of Main loop
                    main = False #break main/outer loop and exit program
                    break #break inner loop

                else: #From previous verifcation, nearby_number is numeric
                    site_index_number = int(nearby_number) - 1 #Python first index is 0, correction
                    nearby_data = get_nearby_places(list_of_sites[site_index_number]) #Given a national site, return a Mapquest API response(formatted)
                    list_of_nearby_places = nearby_places_to_string(nearby_data)
                    for x in list_of_nearby_places:
                        print(x)
                    nearby_navigator = input("Type 'back' to look at the current state or 'exit' to quit: ")

                    #Prompt until back or exit is given
                    while nearby_navigator.lower() not in ['back','exit']:
                        nearby_navigator = input("Type 'back' to look at the current state or 'exit' to quit: ")

                # If the user types 'Back', the loop just continues back to presenting State sites
                # If exit, the inner loop is broken
                if nearby_navigator.lower() == 'exit':
                    main = False
                    break

        if nearby_navigator.lower() != 'exit':
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: **476')

    #Exports/Saves All cached searches
    save_cache(CACHE_DICT)