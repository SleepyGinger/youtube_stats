import requests
import pandas as pd
import json
import datetime
%matplotlib inline

key = *******

def get_stats(stuff):
    stat_url="https://www.googleapis.com/youtube/v3/videos?id="+str(list(stuff)).replace("[","").replace("]","").replace("'","")+"&key="+key+"&part=snippet,contentDetails,statistics,status"
    stat_content=json.loads(requests.get(stat_url).text)
    return stat_content

def channel_id(channel):
    url="https://www.googleapis.com/youtube/v3/channels?part=snippet&forUsername="+channel+"&key="+key

    search_result=json.loads(requests.get(url).text)
    channel_id = search_result['items'][0]['id']
    return str(channel_id)

def video_ID(content):
    id_list=[]
    for video in content['items']:
        listy = video['id']['videoId']
        id_list.append(listy)
    
    return id_list

def build_df(stuff, stats):
    urls=[]
    for x in stuff:
        urls.append("https://www.youtube.com/watch?v="+x)
    
    df = pd.DataFrame(stats)
    df['links']=urls
    df['Date'] = pd.to_datetime(df['Date'], format = "%Y-%m-%dT%H:%M:%S.%fZ")

    days_ago=[]
    for x in df['Date']:
        a = datetime.datetime.now() - x
        a = a.days
        if a == 0:
            a=1
        days_ago.append(a)
    
    df['Days_Ago']=days_ago
    df['Like_Per_Day']=df['Like_Count']/df['Days_Ago']
    df['View_Per_Day']=df['Views']/df['Days_Ago']
    df['Dislike_Per_Day']=df['Dislike_Count']/df['Days_Ago']
    df['Comment_Per_Day']=df['Comments']/df['Days_Ago']
    df['Like_Ratio']=df['Like_Per_Day']/df['View_Per_Day']
    df['Dislike_Ratio']=df['Dislike_Per_Day']/df['View_Per_Day']
    df['Like_vs_Dislike']=df['Dislike_Count']/df['Like_Count']

    df['Like_Ratio']=df['Like_Per_Day']/df['View_Per_Day']
    df['Like_Ratio'] = pd.Series(["{0:.2f}".format(val * 100) for val in df['Like_Ratio']])
    df['Like_Ratio'] = df['Like_Ratio'].astype(float)

    df['Dislike_Ratio']=df['Dislike_Per_Day']/df['View_Per_Day']
    df['Dislike_Ratio'] = pd.Series(["{0:.2f}".format(val * 100) for val in df['Dislike_Ratio']])
    df['Dislike_Ratio'] = df['Dislike_Ratio'].astype(float)
    
    q=df.Date.map(lambda x: x.strftime('%Y-%m-%d'))
    df['short_date']=pd.to_datetime(q, format='%Y-%m-%d')
    
    return pd.DataFrame(df)

def build_stats(chunks):
    temp_dict=[]
    for x in chunks:
        a=get_stats(x)
        temp_dict.append(a)

    stats=[]
    for x in temp_dict:
        for thing in x['items']:
            desc = thing['snippet']['description']
            tit = thing['snippet']['title']
            date = thing['snippet']['publishedAt']
            views = int(thing['statistics']['viewCount'])
            comments = int(thing['statistics']['commentCount'])
            fav = thing['statistics']['favoriteCount']
            img_thum=thing['snippet']['thumbnails']['medium']['url']
            try:
                dislike = int(thing['statistics']['dislikeCount'])
                like = int(thing['statistics']['likeCount'])
            except:
                pass
        
            stats.append({"Description":desc, "Title":tit, "Views": views, "Comments":comments, "Favorite_Count":fav, "Dislike_Count":dislike, "Like_Count":like, "Date":date, "Image Thumb":img_thum})
    return stats
    
name=raw_input('Channel Name: ')
ids=channel_id(name)


url="https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&part=snippet&channelId="+ids+"&maxResults=50&key="+key
content = json.loads(requests.get(url).text)

stuff=[]

stuff = video_ID(content)


num=0

try:
    while num<3:
        next_page=content['nextPageToken'].encode('UTF8')
        content=''
        url = "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount&part=snippet&channelId="+ids+"&maxResults=50&key="+key \
    +"&pageToken="+next_page
        content = json.loads(requests.get(url).text)
        num+=1
    
        for videos in content['items']:
            if videos['id']['kind']=='youtube#video':
                vid_ids=videos['id']['videoId']
                stuff.append(vid_ids)
except:
    pass
            
stuff = [x.encode('UTF8') for x in stuff]
chunks=[stuff[i:i+50] for i  in range(0, len(stuff), 50)]

stats = build_stats(chunks)

df = build_df(stuff, stats)

most_liked=df.sort(columns='Like_Ratio', ascending=0)
most_commentd=df.sort(columns='Comments', ascending=0)
most_disliked=df.sort(columns='Dislike_Ratio', ascending=0)
most_viewed = df.sort(columns='View_Per_Day', ascending=0)
liked = df.sort(columns='Like_vs_Dislike', ascending=1)
dated=df.sort(columns='short_date', ascending=1)

reindex=df.short_date.value_counts().reindex(pd.date_range(min(df.short_date), max(df.short_date)),fill_value=0)
reindex.plot(kind='line', ylim=(-.5, 4), title='Views Over Time', legend=False)

df.plot(x='Date', y='Views', kind='line', title='Views Over Time', legend=False)
df.plot(x='Date', y=['Like_Ratio', 'Dislike_Ratio'], kind='line', title='Like Percentage Over Time', color=["g", "r"])
df.plot(x='Date', y='Dislike_Ratio', kind='line', title='Dislike Percentage Over Time', legend=False)
df.plot(x='Date', y='Like_Ratio', kind='line', title='Like Percentage Over Time', legend=False)

most_liked['links'][:10]
most_viewed['links'][:10]
liked['links'][:10]

