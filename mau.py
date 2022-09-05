#! /usr/bin/env python3

# This file will need to have the execute permission set
# chmod +x ./mau.py

import sys, os, subprocess, json
from ffmpy import FFmpeg, FFprobe
from tinytag import TinyTag


# print('\nEnter album name:')
# album_title = input()

# print('\nEnter album artist:')
# album_artist = input()


# album_featured_artists = []
# cancel = False
# while not cancel:
#     print('\nEnter any additional artists or type "q" to cancel:')
#     artist = input()
#     if artist == 'q':
#         break
#     album_featured_artists.append(artist)


# print('\nEnter album release year')
# album_release_year = int(input())
# print(album_release_year)

# print('\nEnter a description of the album:')
# album_comment = input()

# print('\nEnter number of discs:')
# album_number_of_discs = int(input())


# audio = TinyTag.get('new.alexandria.mp3')
# album = audio.album
# artist = audio.artist
# title = audio.title
# track = audio.track
# duration = audio.duration
# genre = audio.genre
# year = audio.year
# print(year)

def getDuration(mp3):
    ff = FFprobe(
        inputs={ mp3: '-show_entries format=duration -v quiet -of csv="p=0"'},
    )
    duration = ff.run(stdout=subprocess.PIPE)
    duration = duration[0].decode('utf-8')
    duration = duration.strip()
    duration = float(duration)
    return duration

track_list = []

# Loop through all mp3 files and extract ID3 metadata
for filename in os.listdir('.'):
    if filename.endswith('.mp3'):
        audio = TinyTag.get(filename)
        album = audio.album
        artist = audio.artist
        title = audio.title
        track = audio.track
        disc = audio.disc
        genre = audio.genre
        year = audio.year
        duration = getDuration(filename)
        
        candidate_song = {
            "title": title,
            "artitst": artist,
            "featured_artists": [""],
            "disc_number": disc,
            "track_number": track,
            "duration": duration,
            "release_year": year,
            "genres": [genre]
        }

        candidate_song = json.dumps(candidate_song)
        track_list.append(candidate_song)


