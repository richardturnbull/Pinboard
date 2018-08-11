# encoding: utf-8

import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, web, PasswordNotFound

def get_recent_posts(api_key):
    """
    Retrieve recent posts from Pinboard.in
    Returns a list of post dictionaries.
    """
    
    url = 'https://api.pinboard.in/v1/posts/recent'
    params = dict(auth_token=api_key, count=100, format='json')
    r = web.get(url, params)

    # throw an error if request failed
    # Workflow will catch this and show it to the user
    r.raise_for_status()

    # Parse the JSON returned by pinboard and extract the posts
    result = r.json()
    posts = result['posts']
    return posts

def search_key_for_post(post):
    """
    Generate a string search key for a post
    """

    elements = []
    elements.append(post['description'])  # title of post
    elements.append(post['tags'])  # post tags
    elements.append(post['extended'])  # description
    
    return u' '.join(elements)    

def main(wf):

    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    
    # add an optional (nargs='?') --setkey argument and save its
    # value to 'apikey' (dest). This will be called from a separate "Run Script"
    # action with the API key
    parser.add_argument('--setkey', dest='apikey', nargs='?', default=None)
    
    # add an optional query and save it to 'query'
    parser.add_argument('query', nargs='?', default=None)
    
    # parse the script's arguments
    args = parser.parse_args(wf.args)

    ####################################################################
    # Save the provided API key
    ####################################################################
    
    # decide what to do based on arguments
    if args.apikey:  # Script was passed an API key
        # save the key
        wf.save_password('pinboard_api_key', args.apikey)
        
        return 0  # 0 means script exited cleanly

    ####################################################################
    # Check that we have an API key saved
    ####################################################################

    try:
        api_key = wf.get_password('pinboard_api_key')
    except PasswordNotFound:  # API key has not yet been set
        wf.add_item('No API key set.',
                    'Please use pbsetkey to set your Pinboard API key.',
                    valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    ####################################################################
    # View/filter Pinboard posts
    ####################################################################

    query = args.query
    # Retrieve posts from cache if available and no more than 600
    # seconds old

    def wrapper():
        """
        `cached_data` can only take a bare callable (no args),
        so we need to wrap callables needing arguments in a function
        that needs none.
        """
        return get_recent_posts(api_key)

    
    # Retrieve posts from cache if available and no more than 60
    # seconds old
    posts = wf.cached_data('posts', wrapper, max_age=600)

    # If script was passed a query, use it to filter posts
    if query:
        #print "query: {}".format(query)
        posts = wf.filter(query, posts, key=search_key_for_post, min_score=20)
        
    # Loop through the returned posts and add an item for each to
    # the list of results for Alfred
    for post in posts:
        wf.add_item(title=post['description'],
                    subtitle=post['href'],
                    arg=post['href'],
                    valid=True,
                    icon=ICON_WEB)

    # Send the results to Alfred as XML
    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))