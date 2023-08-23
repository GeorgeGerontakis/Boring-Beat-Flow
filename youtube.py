import googleapiclient.discovery

def get_channel_id_from_url(api_key, channel_url):  
    channel_handle = channel_url.split("//")[1].split("/")[1]
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(q=channel_handle, type='channel', part='id', maxResults=1)
    response = request.execute()
    channel_id = response['items'][0]['id']['channelId']
    print(f"    [->] Channel ID -> {channel_id}")
    return channel_id

def get_channel_videos(api_key, channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    videos = []
    next_page_token = None
    while True:
        request = youtube.search().list(part="snippet", channelId=channel_id, maxResults=50, pageToken=next_page_token)
        response = request.execute()
        for item in response["items"]:
            if item["id"]["kind"] == "youtube#video":
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                video_link = f"https://www.youtube.com/watch?v={video_id}"
                print(f"    [+] Adding video {video_title} -> {video_id}")
                videos.append(video_link)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    return videos

def get_links_from_channel(api_key, channel_url):
    print(f"[*] Getting videos from channel url: {channel_url}")
    channel_id = get_channel_id_from_url(api_key, channel_url)
    video_urls = get_channel_videos(api_key, channel_id)
    return video_urls