import requests
import pandas as pd
import json
import datetime

key ='&key=*INSERT_YOUR_API_KEY*'
base_url = 'https://www.googleapis.com/youtube/v3/'
base_url_search = 'https://www.googleapis.com/youtube/v3/search?'
snip = 'part=snippet&maxResults=50'

def gets_id(username):
    url=base_url+"channels?part=snippet&forUsername="+username+key

    search_result=json.loads(requests.get(url).text)
    user_id = search_result['items'][0]['id']
    return str(user_id)

def gets_video_id(content):
    video_ids=[]
    for video in content['items']:
        ids = video['id']['videoId']
        video_ids.append(ids)
    
    return video_ids


def grabs_stats(chunks):
    
    temp_dict=[]
    for x in chunks:
        a=gets_stats(x)
        temp_dict.append(a)

    stats=[]
    for video in temp_dict:
        tags=[]
        for stat in video['items']:
            desc = stat['snippet']['description']
            tit = stat['snippet']['title']
            date = stat['snippet']['publishedAt']
            views = int(stat['statistics']['viewCount'])
            comments = int(stat['statistics']['commentCount'])
            img_thum = stat['snippet']['thumbnails']['medium']['url']
            try:
                dislike = int(stat['statistics']['dislikeCount'])
                like = int(stat['statistics']['likeCount'])
                tags = stat['snippet']['tags']
            except:
                pass
        
            stats.append({"date":date, "image_thumb":img_thum, "tags":tags, "description":desc,"comments":comments, "title":tit, "views": views, "dislike_count":dislike, "like_count":like})
    return stats

def gets_stats(id_list):
    id_list=str(list(id_list)).replace("[","").replace("]","").replace("'","")
    stat_url=base_url+'videos?id='+id_list+'&maxResults=50&part=snippet,contentDetails,statistics,status'+key
    stat_content=json.loads(requests.get(stat_url).text)
    return stat_content

def builds_df(id_list, stats):
    urls=[]
    for one in id_list:
        urls.append("https://www.youtube.com/watch?v="+one)
    
    df = pd.DataFrame(stats)
    df['link']=urls
    df['date'] = pd.to_datetime(df['date'], format = "%Y-%m-%dT%H:%M:%S.%fZ")
    time_format=df.date.map(lambda x: x.strftime('%Y-%m-%d'))
    df['short_date'] = pd.to_datetime(time_format, format='%Y-%m-%d')
    
    days_ago=[]
    for x in df['date']:
        a = datetime.datetime.now() - x
        a = a.days
        if a == 0:
            a=1
        days_ago.append(a)

    df.dislike_count.replace({0:float(1)}, inplace=True)
    df.like_count.replace({0:int(1)}, inplace=True) )}))})
    df['days_ago']=days_ago
    df['comments_view']=df['comments']/df['views']

    df['like_dislike']=df['like_count']/df['dislike_count']
    df['views_day']=df['views']/df['days_ago']
    df['likes_views']=df['like_count']/df['views']
    
    #calculates zscores for stats_cols
    stats_cols=['likes_views', 'like_dislike', 'views_day', 'comments_view']
    for col in stats_cols:
        col_zscore = col + '_z'
        df[col_zscore] = (df[col] - df[col].mean())/df[col].std()
    
    df['multi'] = df['likes_views_z']+df['like_dislike_z']+df['views_day_z']
    df['multi+1'] = df['likes_views_z']+df['like_dislike_z']+df['views_day_z']+df['comments_view_z']
    df['times1']=df['like_dislike']+(df['views_day']+df['likes_views'])
    
    df['like_dislike_rank']=df.like_dislike.rank(ascending=False)
    df['views_day_rank']=df.views_day.rank(ascending=False)
    df['likes_views_rank']=df.likes_views.rank(ascending=False)
    
    
    return pd.DataFrame(df)

def search():    
    query = raw_input('Search: ').replace (" ", "+")
    url = base_url_search+snip+"&q="+query+"&type=video"+key
    content = json.loads(requests.get(url).text)

    stuff=[]
    stuff = gets_video_id(content)

    num=0

    channelTitle = content['items'][0]['snippet']['channelTitle'].capitalize() 
    num_results=float(int(content['pageInfo']['totalResults']))

    while content['nextPageToken'] and num<5:
        next_page=content['nextPageToken'].encode('UTF8')
        content=''
        url = base_url_search+snip+"&q="+query+"&type=video&pageToken="+next_page+key
        content = json.loads(requests.get(url).text)
        num+=1
    
        for videos in content['items']:
            if videos['id']['kind']=='youtube#video':
                vid_ids=videos['id']['videoId']
                stuff.append(vid_ids)
            
    stuff = [x.encode('UTF8') for x in stuff]
    chunks=[stuff[i:i+50] for i  in range(0, len(stuff), 50)]
    
    return chunks, stuff, channelTitle, num_results
    
def channel():
    try:
        name=raw_input('Channel Name: ')
        user_id=gets_id(name)

        url = base_url_search+snip+'&type=video&order=viewCount&channelId='+user_id+key
        content = json.loads(requests.get(url).text)
    
    except:
        user_id=name
        url = base_url_search+snip+'&type=video&order=viewCount&channelId='+user_id+key
        content = json.loads(requests.get(url).text)

    channelTitle=content['items'][0]['snippet']['channelTitle'].capitalize()   

    stuff=[]

    stuff = gets_video_id(content)

    num_results=float(int(content['pageInfo']['totalResults']))
    
    num=0

    try:
        while content['nextPageToken'] and num<20:
            next_page=content['nextPageToken'].encode('UTF8')
            content=''
            url = base_url_search+snip+'&type=video&order=viewCount&channelId='+user_id+'&pageToken='+next_page+key
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
    
    return chunks, stuff, channelTitle, num_results
    
#uncomment this to search 
#chunks, stuff, channelTitle, num_results = search()

#e.g. of channel name: vice from https://www.youtube.com/user/vice
chunks, stuff, channelTitle, num_results = channel()
    
stats=grabs_stats(chunks)

df=builds_df(stuff, stats)

print 'analysing '+str((len(df)/num_results)*100)[:4]+'% of '+channelTitle

top_ranked=df[(df['likes_views_rank']<10) & (df['views_day_rank']<10) & (df['like_dislike_rank']<10)]
most_liked=df[(df['likes_views_rank']<10) & (df['like_dislike_rank']<10)]
popular_like=df[(df['views_day_rank']<10) & (df['like_dislike_rank']<10)]

reindex=df.short_date.value_counts().reindex(pd.date_range(min(df.short_date), max(df.short_date)),fill_value=0)
max_index=max(reindex)+3
reindex.plot(kind='line', ylim=(-1, max_index), title=channelTitle+' Uploads Over Time', legend=False)

df.plot(x='date', y='views', kind='line', title=channelTitle+' Raw Views Over Time', legend=False)
df.sort(columns='views', ascending=0)['link'][:5]

df.plot(x='date', y='views', kind='line', title=channelTitle+' Raw Views Over Time', legend=False)
df.sort(columns='views', ascending=0)['link'][:5]

df.plot(x='date', y='like_dislike', kind='line', title=channelTitle+' Likes VS Dislikes', legend=False, color='y')
df.sort(columns='like_dislike', ascending =0)['link'][:5]

df.plot(x='date', y='views_day', kind='line', title=channelTitle+' Views Per Day', legend=False)
df.sort(columns='views_day_rank', ascending =1)['link'][:5]

df.plot(x='date', y='comments_view', kind='line', title=channelTitle+' Views Per Day', legend=False)
df.sort(columns='comments_view', ascending =0)['link'][:3]

df.plot(x='date', y='likes_views_rank', kind='line', title=channelTitle+' Likes Per View', legend=False, color='g')
df.sort(columns='likes_views_rank', ascending =1)['link'][:3]

df.plot(x='date', y='likes_views_rank', kind='line', title=channelTitle+' Likes Per View', legend=False, color='g')
df.sort(columns='likes_views_rank', ascending =1)['link'][:3]

df.plot(x='date', y='like_count', kind='line', title='Like Percentage Over Time', color="g")
df.plot(x='date', y='dislike_count', kind='line', title='Like Percentage Over Time', color="r")

top_ranked['link']

most_liked['link']

popular_like['link']

#if youd like to export to csv
#df.to_csv('export.csv')