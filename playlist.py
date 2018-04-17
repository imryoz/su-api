
# -*- coding: utf-8 -*-

import os
import time
import flask
import requests
import json
from flask_cors import *
from flask import *
from pymongo import MongoClient
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from urllib.parse import urljoin, parse_qs ,urlparse
import urllib.request

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://mukunda:iwillraise@ds231199.mlab.com:31199/shortup")
db = client.shortup

@app.route('/video',methods=["POST"])
def index1():
  
  link = request.json["link"]
  url_data = urlparse(link)
  query = parse_qs(url_data.query)
  video_id = query["v"][0]
  final = fetch_video(video_id)
  return jsonify(final)

@app.route('/save_video',methods=["POST"])
def save_video():
	collection_name1 = db.viddb
	collection_name2 = db.serdb
	link = request.json["link"]
	url_data = urlparse(link)
	query = parse_qs(url_data.query)
	video_id = query["v"][0]
	final = fetch_video(video_id)
	try:
		if final["videoid"] not in collection_name1.distinct("videoid"):
			playlistName = request.json["playlistName"]
			collection_name2.update({"playlistName":"Mahatalli"},{'$push': {'items': final}})
			collection_name1.insert_one(final)
			return jsonify({"result":"video Sucessfully updated"})
		else:
			return jsonify({"result":"video already exists"})
	except:
		if final["videoid"] not in collection_name1.distinct("videoid"):
			collection_name1.insert_one(final)
			return jsonify({"result":"video Sucessfully uploaded"})
		else:
			return jsonify({"result":"video already exists"})

@app.route('/delete_channel',methods=["POST"])
def dalete_channel():
	collection_name1 = db.viddb
	collection_name2 = db.serdb
	channeltitle = request.json["channeltitle"]
	collection_name2.delete_one({"channeltitle": channeltitle})
	collection_name1.delete_many({"channeltitle": channeltitle})
	return jsonify({"result":"Channel is Sucessfully deleted"})

@app.route('/delete_video',methods=["POST"])
def delete_video():
	collection_name1 = db.viddb
	collection_name2 = db.serdb
	title = request.json["title"]
	playlistName = request.json["playlistName"]
	collection_name1.delete_one({"title":title})
	collection_name2.update({ "playlistName": playlistName },{ "$pull": { 'items': { 'title': title } } })
	return jsonify({"result":"video Sucessfully deleted"})

@app.route('/get_videos',methods=["GET"])
def get_videos():
	collection_name1 = db.viddb
	final_list = []
	for title in collection_name1.distinct("title"):
		final_list.append({"title":title})
	return jsonify(final_list)


@app.route('/fetch_playlist',methods=["POST"])
def fetch_playlist():
	try:
		collection_name = db.serdb
		playlistName = request.json["playlistName"]
		final_playlist = collection_name.find_one({"playlistName":playlistName})
		return jsonify(final_playlist)
	except:
		
		link = request.json["link"]
		url_data = urlparse(link)
		query = parse_qs(url_data.query)
		playlist = query["list"][0]
		final = get_playlist(playlist)
		return jsonify(final)

@app.route('/save_playlist',methods=["POST"])
def save_playlist():
	collection_name1 = db.viddb
	collection_name2 = db.serdb
	serdata = request.json
	playlistId = serdata["playlistId"]
	playlistName = serdata["playlistName"]
	channeltitle = serdata["items"][0]["channeltitle"]
	channelid = serdata["items"][0]["channelid"]
	timecreated = serdata["items"][0]["timecreated"]
	if serdata["update"]==False:
		if playlistId not in collection_name2.distinct("playlistId"):
			if playlistName not in collection_name2.distinct("playlistName"):
				serdata["channeltitle"]=channeltitle
				serdata["channelid"]=channelid

				serdata["timecreated"]=timecreated
				collection_name2.insert(serdata)
				for vid in serdata["items"]:
					vid["playlistName"]=playlistName
					vid["channelid"]=channelid
					vid["channeltitle"]=channeltitle
					collection_name1.insert_one(vid)
				
				return jsonify({"result":"playlist Sucessfully created"})
			else:
				return jsonify({"result":"playlist name already exists"})
		else:
			return jsonify({"result":"playlistId already exist"})
	else:

		for vid in serdata["items"]:
			vid["playlistName"]=playlistName
			collection_name1.update({"playlistName":playlistName}, {"$set": vid})
		serdata["channeltitle"]=channeltitle
		serdata["channelid"]=channelid
		serdata["playlistName"]=playlistName
		collection_name2.update({"playlistName": playlistName}, {"$set": serdata})
		
		return jsonify({"result":"playlist Sucessfully updated"})

@app.route('/channellist',methods=["GET"])
def channellist():
  collection_name = db.serdb
  final_list = []
  channel_list = collection_name.distinct("channeltitle")
  for channel in channel_list:
    final_list.append({"channeltitle":channel})
  return jsonify({"result":final_list})

@app.route('/createvideo',methods=["POST"])
def video():
  collection_name = db.viddb
  viddata = request.json
  url_data = urlparse(viddata["id"])
  query = parse_qs(url_data.query)
  video_id = query["v"][0]

  for vid_id in viddata["items"]:
    
    if vid_id["id"] not in collection_name.distinct("videoid"):
      collection_name.insert_one({"videoid":video_id,
        "genre":vid_id["genre"],
        "starttime":vid_id["starttime"],
        "playlistId":vid_id["playlistId"],
        "endtime":vid_id["endtime"],
        "title":vid_id["snippet"]["title"],
        "channeltitle":vid_id["snippet"]["channelTitle"],
        "channelid":vid_id["snippet"]["channelId"],
        "description":vid_id["snippet"]["description"],
        "thumbnails":vid_id["snippet"]["thumbnails"],
        "tags":vid_id["snippet"]["tags"],
        "view":vid_id["statistics"]["viewCount"],
        "likes":vid_id["statistics"]["likeCount"],
        "timecreated":time.time()})
      return jsonify({"request":"Video Sucessfully added"})
    else:
      return jsonify({"request":"Video Already exist"})

@app.route('/getplaylistname',methods=["GET"])
def getplaylistnames():
	collection_name = db.serdb
	final_list = []
	for playlistName in collection_name.distinct("playlistName"):
		final_list.append({"playlistName":playlistName})
	return jsonify({"playlist":final_list})

@app.route('/delete_playlist',methods=["POST"])
def delete_playlist():
	collection_name1 = db.serdb
	collection_name2 = db.viddb
	playlistName = request.json["playlistName"]
	collection_name1.delete_one({"playlistName": playlistName})
	collection_name2.delete_many({"playlistName": playlistName})
	return jsonify({"result":"Sucessfully deleted"})


def fetch_video(vidid):

  url = 'https://www.googleapis.com/youtube/v3/videos?part=statistics%2C+snippet&id='+vidid+'&key=AIzaSyAu-AkhctqIxisH7Jtetzf8cgRfqJHMNbo'
  r = requests.get(url)
  vid_data=json.loads(r.content)
  for stat in vid_data["items"]:
    chanid = stat["snippet"]["channelId"]
    chantitle = stat["snippet"]["channelTitle"]
    description = stat["snippet"]["description"]
    title = stat["snippet"]["title"]
    thumbnails = stat["snippet"]["thumbnails"]
    stats = stat["statistics"]
    vidid = stat["id"]

    if "tags" in stat["snippet"].keys():
    	tags = stat["snippet"]["tags"]
    else:
    	tags = []

    if "playlistId" in stat["snippet"].keys():
    	playlistId = stat["snippet"]["playlistId"]
    else:
    	playlistId = ""

    if "playlistName" in stat["snippet"].keys():
    	playlistName = stat["snippet"]["playlistName"]
    else:
    	playlistName = ""

    final_vid={"videoid":vidid,"title":title,"channelid":chanid,"channeltitle":chantitle,"tags":tags,"description":description,"thumbnails":thumbnails,"statistics":stats,"timecreated":time.time(),"playlistId":playlistId,"playlistName":playlistName}
  return (final_vid)

def get_playlist(playlist):
	
	url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId="+playlist+"&key=AIzaSyAu-AkhctqIxisH7Jtetzf8cgRfqJHMNbo"
	r = requests.get(url)
	ser_data=json.loads(r.content)
	final_playlist_list = []
	final_playlist = {}
	for stat in ser_data["items"]:
		video_id = stat["snippet"]["resourceId"]["videoId"]
		resp = fetch_video(video_id)
		playlist_id = stat["snippet"]["playlistId"]
		resp["playlistId"]=playlist_id
		final_playlist_list.append(resp)
	final_playlist["items"]=final_playlist_list
	final_playlist["playlistId"]=playlist_id
	return final_playlist


#watch page

@app.route('/user_series',methods=["POST"])
def user_series():
	collection_name1 = db.serdb
	lang = request.json["language"]
	for series in collection_name1.find({"language":lang},{"_id":0}).limit(12):
		return jsonify({"series":series})

@app.route('/user_videos',methods=["POST"])
def user_videos():
	collection_name2 = db.viddb
	final_list = []
	lang = request.json["language"]
	for video in collection_name2.find({"language":lang},{"_id":0}).limit(12):
		final_list.append({"video":video})
	return jsonify({"videos":final_list})

@app.route('/genre',methods=["POST"])
def genre():
	collection_name2 = db.viddb
	genre = request.json["genre"]
	lang = request.json["language"]
	final_list = []
	for video in collection_name2.find({ "$and": [ { "genre": genre}, { "language": lang }]},{"_id":0}):
		final_list.append({"video":video})
	return jsonify({"video":final_list})

if __name__ == '__main__':
  app.run('localhost', 8090, debug=True)
  