#! /usr/bin/env python3

# This file will need to have the execute permission set
# chmod +x ./mau.py

import sys

print('\nEnter album name:')
album_title = input()

print('\nEnter album artist:')
album_artist = input()


album_featured_artists = []
cancel = False
while not cancel:
    print('\nEnter any additional artists or type "q" to cancel:')
    artist = input()
    if artist == 'q':
        break
    album_featured_artists.append(artist)


print('\nEnter album release year')
album_release_year = int(input())
print(album_release_year)

print('\nEnter a description of the album:')
album_comment = input()


