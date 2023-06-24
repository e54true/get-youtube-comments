from dotenv import load_dotenv
import os
from flask import Flask, render_template, request
#from flask_lt import run_with_lt
from googleapiclient.discovery import build
import re

# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數中獲取 API 金鑰
api_key = os.getenv("API_KEY")

app = Flask(__name__)
#run_with_lt(app)

app.debug = True


# 建立 YouTube Data API 客戶端
youtube = build("youtube", "v3", developerKey=api_key)

# 設定要擷取的資訊（留言內容和作者的資訊）
part = "snippet"

# 設定每次擷取的最大結果數（最多為100）
max_results = 100

# 定義一個函式，用於遞迴處理留言和回覆
def process_comments(comment_thread, comments_dict):
    comment = comment_thread["snippet"]["topLevelComment"]["snippet"]
    comment_text = comment["textDisplay"]
    comment_author = comment["authorDisplayName"]
    comments_dict[comment_text] = []

    # 獲取回覆的留言
    comment_id = comment_thread["id"]
    replies_response = youtube.comments().list(
        part=part,
        parentId=comment_id,
        maxResults=max_results
    ).execute()

    if "items" in replies_response:
        replies = replies_response["items"]
        for reply in replies:
            reply_text = reply["snippet"]["textDisplay"]
            reply_author = reply["snippet"]["authorDisplayName"]
            comments_dict[comment_text].append(reply_text)

    # 檢查是否有下一頁回覆
    while "nextPageToken" in replies_response:
        next_page_token = replies_response["nextPageToken"]
        replies_response = youtube.comments().list(
            part=part,
            parentId=comment_id,
            maxResults=max_results,
            pageToken=next_page_token
        ).execute()

        if "items" in replies_response:
            replies = replies_response["items"]
            for reply in replies:
                reply_text = reply["snippet"]["textDisplay"]
                reply_author = reply["snippet"]["authorDisplayName"]
                comments_dict[comment_text].append(reply_text)

@app.route('/', methods=['GET', 'POST'])
def show_comments():
    try:
        if request.method == 'POST':
            video_url = request.form['video_url']
            #video_id_match = re.search(r"(?<=v=|\/v\/|\/embed\/|youtu.be\/|\/v=|\/e\/|youtu.be\/|\/embed\/|\/v\/|\/e\/)[^#?\&\n]*", video_url)
            #video_id_match = re.search(r"(?<=v=|\/v\/|\/embed\/|youtu.be\/|\/v=|\/e\/|youtu.be\/|\/embed\/|\/v\/|\/e\/)[^#?\&\n]+", video_url)
            video_id = video_url.split("v=")[1].split("&")[0]




        
            #video_id = video_id_match.group(0)
            comments_dict = {}

            print("Fetching comments...")

            response = youtube.commentThreads().list(
                part=part,
                videoId=video_id,
                maxResults=max_results
            ).execute()

            print("Comments fetched successfully.")

            # 獲取第一頁的留言
            comments = response["items"]
            for comment in comments:
                process_comments(comment, comments_dict)

            # 檢查是否有下一頁留言
            while "nextPageToken" in response:
                next_page_token = response["nextPageToken"]
                response = youtube.commentThreads().list(
                    part=part,
                    videoId=video_id,
                    maxResults=max_results,
                    pageToken=next_page_token
                ).execute()

                comments = response["items"]
                for comment in comments:
                    process_comments(comment, comments_dict)

            print("Rendering template...")        

            return render_template('comments.html', comments=comments_dict)
    
        return render_template('index.html')

    except Exception as e:
        app.logger.error("發生錯誤：" + str(e))
        print("發生錯誤：" + str(e))
        return "<h1>Error</h1><p>發生錯誤，請查看終端機以獲取詳細信息。</p>"


if __name__ == '__main__':
    app.run()

