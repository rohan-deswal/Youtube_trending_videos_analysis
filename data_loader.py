#!/usr/bin/env python
# coding: utf-8

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import json

import urllib
from sqlalchemy import create_engine

import pandas as pd
import numpy as np

import datetime


scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


api_service_name = "youtube"
api_version = "v3"


#api key
api_key = "<API Key>"

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=api_key)


countries = ['CA', 'DE', 'FR', 'GB', 'IN', 'JP', 'KR', 'MX', 'RU', 'US']


def get_video_list(country_code):

    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=country_code,
        maxResults=50,
    )
    response = request.execute()
    final_response = {'items': response['items']}

    while "nextPageToken" in response.keys():
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=country_code,
            maxResults=50,
            pageToken=response['nextPageToken']
        )
        response = request.execute()
        final_response['items'] += response['items']

    return final_response


def create_video_list_table(response, country_code):
    df = pd.json_normalize(response['items'])
    df_new = pd.DataFrame()
    
    df_new['id'] = df['id']
    df_new['title'] = df['snippet.title']
    df_new['channel'] = df['snippet.channelTitle']
    df_new['channel_id'] = df['snippet.channelId']
    df_new['description'] = df['snippet.description']
    df_new['thumbnail'] = df['snippet.thumbnails.default.url']
    df_new['category'] = df['snippet.categoryId'].astype('int')
    df_new['view_count'] = df['statistics.viewCount'].astype('int')
    df_new['like_count'] = df['statistics.likeCount'].astype('Int64')
    df_new['comment_count'] = df['statistics.commentCount'].astype('Int64')
    df_new['publish_date'] = pd.to_datetime(df['snippet.publishedAt'])
    
    df_new['trending_date'] = pd.to_datetime('today').normalize()
    
    df_new['country'] = country_code
    
    df_new = df_new.reset_index()
    df_new = df_new.rename(columns={"index":"rank"})
    df_new['rank'] = df_new.index + 1
    
    df_new = df_new.set_index('id')
    
    return df_new


def to_db(categories, video_list, country_code):
    
    category_table_name = "videoCategories"
    table_name = "trendingVideos"
    
    
    try:
        categories.head(n=0).to_sql(name=category_table_name, con=engine, if_exists="replace")
    except ValueError:
        pass
    finally:
        categories.to_sql(name=category_table_name, con=engine, if_exists="append")
    
    
    try:
        video_list.head(n=0).to_sql(name=table_name, con=engine, if_exists="fail")
    except ValueError:
        pass
    finally:
        video_list.to_sql(name=table_name, con=engine, if_exists="append")



if __name__ == "__main__":
    username = 'root'
    password = 'root'
    host = '4.240.82.255'
    db_name = 'youtube_db'

    postgres_url = f'postgresql://{username}:{password}@{host}:5432/{db_name}'

    engine = create_engine(postgres_url)


    for country in countries:
        response = get_video_categories(country)
        categories = create_category_table(response)
        
        response = get_video_list(country)
        video_list = create_video_list_table(response, country)
        
        to_db(categories, video_list, country)
        
        print(f"Uploaded for country {country}")
    

