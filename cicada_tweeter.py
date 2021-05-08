# -*- coding: utf-8 -*-
"""
Created on Thu May  6 21:56:14 2021

@author: mvanstav
"""

import os
import io
import tweepy
import requests
import configparser

def get_api(api_key, api_secret, access_token, access_token_secret):
    """
    set up the API and verify that the credentials worked.

    Returns the api handler
    """
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    api.verify_credentials()
    
    return api

def send_tweet(api, serveraddress):
    """
    grabs the temperature data off Erik's webserver
    formats a tweet string
    formats alt text
    uploads an image
    sends the tweet

    Returns
    -------
    None.

    """
    info = requests.get(f'http://{serveraddress}/latestjson/temp_f').json()
    temp = info['latest_val']
    if temp < 64:
        tweetstring = f"The current ground temperature is {temp:.1f} degrees F, which is below the target temperature. Cicadas are cozy in their burrows."
    elif 64 < temp <= 65.5:
        tweetstring = f"The current ground temperature is {temp:.1f}, which might be warm enough for the cicadas to emerge."
    else:
        tweetstring = f"The current ground temperature is {temp:.1f}, which probably means the cicadas are on the loose!"
    print(tweetstring)
    
    image = requests.get(f'http://{serveraddress}/png/temp_f', stream=True)
    bio = io.BytesIO(image.raw.read())
    bio.seek(0)
    
    trend_map = {-1:'decreasing', 0:'staying the same', 1:'increasing'}
    trend = info['trend_2hr']
    minval = info['min_24hr']
    maxval = info['max_24hr']
    
    altstring = (f"A plot of temperature versus time for the last 48 hours. There is a horizontal "
                 f"red line marking 64 degrees F. The temperature is currently {trend_map[trend]}. In the last 24 hours, the "
                 f"minimum value was {minval:.1f} and the maximum value was {maxval:.1f}")
    
    print(altstring)
    
    image_upload = api.media_upload("cicada_temp_f.png", file=bio)
    api.create_media_metadata(media_id = image_upload.media_id, alt_text = altstring)
    api.update_status(tweetstring, media_ids = [image_upload.media_id])


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.split(__file__)[0], 'cicada_tweeter.cfg'))
    ct_cfg = config['cicada_tweeter']

    api = get_api(ct_cfg['APIkey'], ct_cfg['APIsecret'], ct_cfg['AccessToken'], ct_cfg['AccessTokenSecret'])
    
    send_tweet(api, ct_cfg['serveraddress'])



##################
# MARIE look up how to get the API to raise exceptions
# look up f string formatting to fix sig figs
# email Erik the config file
############
