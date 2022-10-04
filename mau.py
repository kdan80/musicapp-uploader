#! /usr/bin/env python3

# This file will need to have the execute permission set
# chmod +x ./mau.py

import os, subprocess, json, math
from ffmpy import FFprobe
from tinytag import TinyTag
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error
import os, sys
import requests

load_dotenv()

BUCKET = os.environ.get("BUCKET")
SERVER = os.environ.get("SERVER")
ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
UPLOAD_URL = os.environ.get("UPLOAD_URL")

client = Minio(
            SERVER,
            secure=False,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
        )

def checkBucketExists(bucket):
    return client.bucket_exists(bucket)

def createBucket(bucket):
    try:
        client.make_bucket(bucket)
    except S3Error as err:
        print("Bucket creation error: ", err)
        print("Exiting...")
        sys.exit(1)

def uploadFile(bucket, artist, album, file):
    try:
        filename = f"{artist}/{album}/{os.path.basename(file)}"
        client.fput_object(bucket, filename, file)
        print(f"{filename} was uploaded")
    except S3Error as err:
        print("File upload error: ", err)
        print("Exiting...")
        sys.exit(1)

# Before we do anything check the minio bucket exists
bucketExists = checkBucketExists(BUCKET)
if not bucketExists:
    createBucket(BUCKET)

# Magic numbers/file signatures
file_sigs = {
    '.jpg': 'ffd8ffe',
    '.png': '89504e470d0a1a0a',
    '.bmp': '424d'
}

def getImageFileExt(hex_img):
    hex_img = hex_img.lower()
    if hex_img[0:7] == 'ffd8ffe':
        return '.jpg'
    if hex_img[0:15] == '89504e470d0a1a0a':
        return '.png'
    return 'unknown'

def getDuration(mp3):
    ff = FFprobe(
        inputs={ mp3: '-show_entries format=duration -v quiet -of csv="p=0"'},
    )
    duration = ff.run(stdout=subprocess.PIPE)
    duration = duration[0].decode('utf-8')
    duration = duration.strip()
    duration = float(duration)
    duration = int(math.floor(duration))
    return duration

track_list = []
album_duration = 0
album_artist = ''
album_title = ''
album_comment = ''
album_release_year = 0000
album_number_of_discs = 1
album_featured_artists = []
album_genres = []
album_art = ''
image_data = None

# Grab the comment from comment.txt
with open('comment.txt', 'r') as file:
    album_comment = file.read().replace('\n', '')

# Loop through all mp3 files and extract ID3 metadata
for filename in os.listdir('.'):
    rack_featured_artistst = []

    if filename.endswith('.mp3'):
        #print(os.path.abspath(filename))

        # Extract ID3 tags from audio files
        audio = TinyTag.get(filename, image=True)
        track_artist = audio.albumartist
        track_title = audio.title
        track_disc = int(audio.disc.lstrip('0'))
        track_number = int(audio.track.lstrip('0'))
        track_genres = audio.genre.split(' / ')
        track_year = int(audio.year)
        track_filename = filename
        track_path = os.path.abspath(filename)

        # Get the cover art
        if not image_data:
            image_data = audio.get_image()

            if image_data != None:
                image_data_hex = image_data.hex()
                image_ext = getImageFileExt(image_data_hex)
                if image_ext != 'unknown':
                    album_art = f'album_art{image_ext}'
                    with open(album_art, 'wb') as file:
                        file.write(image_data)

        # Get the relevant album metadata
        album_artist = audio.albumartist
        album_title = audio.album
        album_release_year = audio.year

        # Split artists into an array, (ID3 artist tags should be separated by ' / ')
        track_featured_artists = audio.artist.split(' / ')

        # Get individual track duration and calculate album total duration
        track_duration = getDuration(filename)
        album_duration += track_duration

        # Get all the featured artists (compilations, soundtracks etc may have many artists)
        for artist in track_featured_artists:
            if artist not in album_featured_artists:
                album_featured_artists.append(artist)

        # Do the exact same thing for genres
        for genre in track_genres:
            if genre not in album_genres:
                album_genres.append(genre)

        # Calculate number of discs
        if (int(track_disc) > int(album_number_of_discs)):
            album_number_of_discs = track_disc

        # Take all the extracted metadata and compile an object to represent each track
        candidate_song = {
            "title": track_title,
            "artist": track_artist,
            "featured_artists": track_featured_artists,
            "disc_number": track_disc,
            "track_number": track_number,
            "duration": int(math.floor(track_duration)),
            "release_year": track_year,
            "filename": track_filename,
            "genres": track_genres
        }
        #candidate_song = json.dumps(candidate_song)
        track_list.append(candidate_song)

        # Upload the file to minio bucket
        uploadFile(BUCKET, album_artist, album_title, track_path)

# Create a json representation of the album ID3 metadata and write it to an info.json file
album = {
    "title": album_title,
    "artist": album_artist,
    "featured_artists": album_featured_artists,
    "track_list": track_list,
    "duration": int(math.floor(album_duration)),
    "release_year": album_release_year,
    "comment": album_comment,
    "number_of_discs": album_number_of_discs,
    "album_art": album_art,
    "genres": album_genres
}
album = json.dumps(album)

f = open("info.json", "w")
f.write(album)
f.close()

# Upload the json file and album art to the minio bucket
uploadFile(BUCKET, album_artist, album_title, album_art)
#uploadFile(BUCKET, album_artist, album_title, "info.json")

req = requests.post(UPLOAD_URL, json={
    "album": album_title,
    "artist": album_artist,
    "comment": album_comment,
    "info": {
        "title": album_title,
        "artist": album_artist,
        "featured_artists": album_featured_artists,
        "track_list": track_list,
        "duration": int(math.floor(album_duration)),
        "release_year": album_release_year,
        "comment": album_comment,
        "number_of_discs": album_number_of_discs,
        "album_art": album_art,
        "genres": album_genres
    }
})

print("Status: ", req.text)