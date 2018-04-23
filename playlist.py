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
	collection_name3 = db.channel
	details = request.json
	channeltitle = details["channeltitle"]
	language = details["language"]
	# link = request.json["link"]
	# url_data = urlparse(link)
	# query = parse_qs(url_data.query)
	# video_id = query["v"][0]
	# final = fetch_video(video_id)
	# try:
	if details["title"] not in collection_name1.distinct("title"):
		playlistName = request.json["playlistName"]
		collection_name2.update({"playlistName":playlistName},{'$push': {'items': details}})
		collection_name1.insert_one(details)
		collection_name3.update({"channeltitle":channeltitle}, {"$set": {"channeltitle":channeltitle,"language":language}},upsert=True)
		return jsonify({"result":"video Sucessfully updated"})
	else:
		return jsonify({"result":"video already exists"})
	# except:
	# 	if details["videoid"] not in collection_name1.distinct("videoid"):
	# 		collection_name1.insert_one(details)
	# 		collection_name3.update({"channeltitle":details["channeltitle"]}, {"$set": {"channeltitle":details["channeltitle"],"language":details["language"]}},upsert=True)
	# 		return jsonify({"result":"video Sucessfully uploaded"})
	# 	else:
	# 		return jsonify({"result":"video already exists"})

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
	titles = collection_name1.aggregate([{"$group": { "_id": { "title": "$title", "playlistName": "$playlistName"}}}])
	for title in titles:

		final_list.append({"title":title['_id']['title'],"playlistName":title['_id']['playlistName']})
	return jsonify(final_list)

@app.route('/get_video_details',methods=["POST"])
def get_video_details():
	collection_name1 = db.viddb
	title = request.json["title"]
	video = collection_name1.find_one({"title":title},{"_id":0})
	return jsonify(video)


@app.route('/update_video_details',methods=["POST"])
def update_video_details():
	collection_name1 = db.viddb
	collection_name2 = db.serdb
	data = request.json
	title = data["title"]
	playlistName = data["playlistName"]
	collection_name1.update({"title":title}, {"$set": data})
	collection_name2.update({"playlistName": playlistName,"items.title": title},{"$set":{"items.$":data}})
	return jsonify({"result":"video Sucessfully updated"})

@app.route('/fetch_playlist',methods=["POST"])
def fetch_playlist():
	try:
		collection_name = db.serdb
		playlistName = request.json["playlistName"]
		final_playlist = collection_name.find_one({"playlistName":playlistName},{"_id":0})
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
	collection_name3 = db.channel
	serdata = request.json
	playlistId = serdata["playlistId"]
	playlistName = serdata["playlistName"]
	language = serdata["language"]
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
				collection_name3.update({"channeltitle":channeltitle}, {"$set": {"channeltitle":channeltitle,"language":language}},upsert=True)	
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
		collection_name3.update({"channeltitle":channeltitle}, {"$set": {"channeltitle":channeltitle,"language":language}},upsert=True)
		
		return jsonify({"result":"playlist Sucessfully updated"})

##channel adding
@app.route('/channellist',methods=["GET"])
def channellist():
  collection_name = db.channel
  final_list = []
  channel_list = collection_name.find({},{"_id":0})
  for channel in channel_list:
    final_list.append(channel)
  return jsonify({"result":final_list})

@app.route('/addchannel',methods=["POST"])
def addchannel():
	collection_name = db.channel
	channeltitle = request.json["channeltitle"]
	image = request.json["image"]
	lang = request.json["language"]
	final = {"channeltitle":channeltitle,"image":image, "language":lang}
	collection_name.update({"channeltitle":channeltitle},{"$set":final},upsert=True)
	return jsonify({"result":"image Sucessfully uploaded"})

@app.route('/delete_channel',methods=["POST"])
def delete_channel():
	collection_name1 = db.serdb
	collection_name2 = db.viddb
	collection_name3 = db.channel
	channeltitle = request.json["channeltitle"]
	collection_name1.delete_one({"channeltitle": channeltitle})
	collection_name3.delete_one({"channeltitle": channeltitle})
	collection_name2.delete_many({"channeltitle": channeltitle})
	return jsonify({"result":"Sucessfully deleted channel"})

## ADDvert adding
@app.route('/addadvert',methods=["POST"])
def addadvert():
	collection_name = db.advert
	title = request.json["title"]
	image = request.json["image"]
	lang = request.json["language"]
	final = {"title":title,"image":image,"language":lang}
	collection_name.update({"title":title},{"$set":final},upsert=True)
	return jsonify({"result":"image Sucessfully uploaded"})

@app.route('/get_advert',methods=["GET"])
def get_advert():
	collection_name = db.advert
	final_list = []
	for add in collection_name.find({},{"_id":0}):
		final_list.append({"addvert":add})
	return jsonify({"advert":final_list})

@app.route('/deleteadvert',methods=["POST"])
def deleteadvert():
	collection_name = db.advert
	title = request.json["title"]
	collection_name.delete_one({"title": title})
	return jsonify ({"result":"Sucessfully deleted"})

##background images adding
@app.route('/addbackground',methods=["POST"])
def addbackground():
	collection_name = db.background
	title = request.json["title"]
	image = request.json["image"]
	final = {"title":title,"image":image}
	collection_name.update({"title":title},{"$set":final},upsert=True)
	return jsonify({"result":"image Sucessfully uploaded"})

@app.route('/get_background',methods=["GET"])
def get_background():
	collection_name = db.background
	final_list = []
	for background in collection_name.find({},{"_id":0}):
		final_list.append({"background":background})
	return jsonify({"background":final_list})

@app.route('/deletebackground',methods=["POST"])
def deletebackground():
	collection_name = db.background
	title = request.json["title"]
	collection_name.delete_one({"title": title})
	return jsonify ({"result":"Sucessfully deleted"})

@app.route('/createvideo',methods=["POST"])
def video1():
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
    	tags = list(map(lambda x: str.replace(x, " ", ""), tags))
    	tags = list(map(lambda x: x.lower(),tags))
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
	final_list = []
	for series in collection_name1.find({"language":lang},{"_id":0}).sort('timecreated', -1).limit(12):
		final_list.append({"series":series})
	return jsonify({"series":final_list})

@app.route('/loadmore_series',methods=["POST"])
def loadmore_series():
	collection_name1 = db.serdb
	lang = request.json["language"]
	final_list = []
	for series in collection_name1.find({"language":lang},{"_id":0}).sort('timecreated', -1):
		final_list.append({"series":series})
	return jsonify({"series":final_list})

@app.route('/genre',methods=["POST"])
def genre():
	collection_name2 = db.viddb
	genre = request.json["genre"]
	lang = request.json["language"]
	final_list = []
	for video in collection_name2.find({ "$and": [ { "genre": genre}, { "language": lang }]},{"_id":0}):
		final_list.append({"video":video})
	return jsonify({"video":final_list})

@app.route('/recentrelease',methods=["POST"])
def recentrelease():
	collection_name2 = db.viddb
	lang = request.json["language"]
	final_list = []
	for video in collection_name2.find({"language":lang},{"_id":0}).sort('timecreated', -1).limit(12):
		final_list.append({"video":video})
	return jsonify({"videos":final_list})

@app.route('/loadmore_recentrelease',methods=["POST"])
def loadmore_recentrelease():
	collection_name2 = db.viddb
	lang = request.json["language"]
	final_list = []
	for video in collection_name2.find({"language":lang},{"_id":0}).sort('timecreated', -1):
		final_list.append({"video":video})
	return jsonify({"videos":final_list})

@app.route('/getchannels',methods=["POST"])
def getchannels():
	collection_name = db.channel
	lang = request.json["language"]
	final_list = []
	for channel in collection_name.find({"language":lang},{"_id":0}):
		final_list.append({"channel":channel})
	return jsonify({"videos":final_list})

@app.route('/user_series_byid',methods=["POST"])
def user_series_byid():
	collection_name = db.serdb
	collection_name1 = db.viddb
	playlistName = request.json["playlistName"]

	if len(playlistName)>2:
		for playlist in collection_name.find({"playlistName":playlistName},{"_id":0}):
			return jsonify({"playlist":playlist})
	else:
		lang = request.json["language"]
		genre = request.json["genre"]
		final_list = []
		for video in collection_name1.find({ "$and": [ { "genre": genre}, { "language": lang }]},{"_id":0}):
			final_list.append({"video":video})
		return jsonify({"video":final_list})

@app.route('/trending',methods=['POST'])
def trending():
	collection_name = db.trending
	collection_name1 = db.viddb
	stack = request.json["titles"]
	for title in titles:
		for video in collection_name1.find({"title":title},{"_id":0}):
			collection_name.insert_one(video)
	return jsonify({"result":"Trending Sucessfully uploaded"})

# @app.route('/updatetrending',methods=['POST'])
# def updatetrending():


@app.route('/search',methods=["POST"])
def search():
	collection_name1 = db.viddb
	final_list = []
	search_str = request.json["search_string"]
	search_str = search_str.replace(" ","").lower()
	for vid_data in collection_name1.find({},{"_id":0}):
		if next((True for co in vid_data["tags"] if search_str in co), False)==True:
			final_list.append({"video":vid_data})
	return jsonify({"video":final_list})

if __name__ == '__main__':
  app.run('localhost', 8090, debug=True)
  
