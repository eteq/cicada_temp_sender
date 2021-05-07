# -*- coding: utf-8 -*-
"""
Created on Thu May  6 21:56:14 2021

@author: mvanstav
"""

import tweepy
import requests
import io
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
        tweetstring = f"The current ground temperature is {temp} degrees F, which is below the target temperature. Cicadas are cozy in their burrows."
    elif 64 < temp <= 65.5:
        tweetstring = f"The current ground temperature is {temp}, which might be warm enough for the cicadas to emerge."
    else:
        tweetstring = f"The current ground temperature is {temp}, which probably means the cicadas are on the loose!"
    print(tweetstring)
    
    image = requests.get(f'http://{serveraddress}/png/temp_f', stream=True)
    bio = io.BytesIO(image.raw.read())
    bio.seek(0)
    
    trend_map = {-1:'decreasing', 0:'staying the same', 1:'increasing'}
    trend = info['trend_2hr']
    minval = info['min_24hr']
    maxval = info['max_24hr']
    
    altstring = (f"A plot of temperature versus time starting from 9pm on May 5th. There is a horizontal "
                 f"red line marking 64 degrees F. The temperature is currently {trend_map[trend]}. In the last 24 hours, the "
                 f"minimum value was {minval} and the maximum value was {maxval}")
    
    print(altstring)
    
    image_upload = api.media_upload("cicada_temp_f.png", file=bio)
    api.create_media_metadata(media_id = image_upload.media_id, alt_text = altstring)
    api.update_status(tweetstring, media_ids = [image_upload.media_id])




if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(r'cicada_tweeter.cfg')
    ct_cfg = config['cicada_tweeter']
    
    # These are the credentails for the new bot account
    #APIkey = "AaZeKnOxJoj0QnX1O8vScxXhg"
    #APIsecret = "s6hxgDwYZC0gV7EGaG4BTTHipBYGSsqsmhUmOIkw5RGgwYSGd0"
    #BearerToken = "AAAAAAAAAAAAAAAAAAAAAP1OPQEAAAAAxnvxzzY6I%2FdDF4iJdfEG2BShbiM%3DFwHYP9WRQXwRmtYu4YzJY0VQl0frw5IDkdIqV2ST6m6SSYUHAJ"
    #AccessToken = "1390679839837937672-vmD3YtURc6WL9MbwjrLgotaAGwjuoW"
    #AccessTokenSecret = "PbGuOLHppxLJKGUd5VdztdS9esH3DJfS2J28nThd6WFJ6"
    
    api = get_api(ct_cfg['APIkey'], ct_cfg['APIsecret'], ct_cfg['AccessToken'], ct_cfg['AccessTokenSecret'])
    
    send_tweet(api, ct_cfg['serveraddress'])



##################
# MARIE look up how to get the API to raise exceptions
# look up f string formatting to fix sig figs
############