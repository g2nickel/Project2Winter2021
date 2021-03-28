#################################
##### Name: Greg Nickel  ########
##### Uniqname: gnickel  ########
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_DICT = {}

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
        zipcode = soup.find('span', class_='postal-code').text.strip()
        state = soup.find('span', class_='region').text.strip()
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
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    pass

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
        cache_file = open(cache.json, 'r')
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
    fw = open(cache.json,"w")
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


if __name__ == "__main__":
    #initial variables
    CACHE_DICT= open_cache()
    state_url_dict = build_state_url_dict()
    print("Welcome the the National Sites Finder!")

    #Begin user-interface
    state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: ')
    while True:
        state = state.lower() #Make search/state lower case

        if state in ("exit","quit","exi"): #defensive programming
            break
        #Gives users another option for lists of states, including examples of Territory/Non-states
        if state == 'help':
            key = list(state_url_dict.keys())
            print(f"Examples of states include: {key[0].title()}, {key[1].title()}, {key[2].title()}, {key[3].title()} and many more...")
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit: ')
            continue

        #Check and see if user entered an abbreviation rather than a state name
        abbrev = state_abbreviations_maker(state,state_url_dict)
        if abbrev in state_url_dict.keys():
            check = input(f'You typed "{state.upper()}"", but did you mean "{abbrev.title()}"? Type "Yes" or "No" ')
            if check.lower() in ['y', 'ye', 'yes']:
                state = abbrev

        if state not in state_url_dict.keys():
            print("That doesn't appear to be a state. Please try again.")
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: ')
            continue

        if state in state_url_dict.keys():
            state_url = state_url_dict[state]
            list_of_sites = get_sites_for_state(state_url)
            print(70*"-")
            if state == "ohio":
                print("Here are the National Sites in the state of Ohio.")
            elif state in ['american samoa', 'guam', 'virgin islands', 'northern mariana islands']:
                if state in ['virgin islands', 'northern mariana islands']:
                    print(f"Here are the National Sites in the beautiful territory of the {state.title()}.")
                else:
                    print(f"Here are the National Sites in the beautiful territory of {state.title()}.")
            elif state == 'district of columbia':
                print(f"Here are the National Sites in the nation's capitol.")
            else:
                print(f"Here are the National Sites in the lovely state of {state.title()}")
            print(70*"-")

            counter = 1
            for site in list_of_sites:
                print(f"[{counter}] {site.info()}")
                counter += 1

            state = input('Enter a state name (e.g. Michigan, michigan) or "exit" to quit or "help" for more info: ')
            continue

