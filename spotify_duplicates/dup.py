#! /bin/env python

import re
import sys
import csv
import spotipy
from itertools import groupby
from operator import itemgetter
from dataclasses import dataclass
from spotipy.oauth2 import SpotifyClientCredentials

@dataclass
class PlaylistItem:
    name: str
    artist: str
    added_at: str
    added_by: str

    def __init__(self, name: str, added_at: str, added_by: str, artists: list[str]):
        self.name = name
        self.artist = ','.join(sorted(map(lambda x: x['name'], artists)))
        self.added_at = added_at
        self.added_by = added_by

    def key(self) -> str:
        return self.name + ':' + self.artist

class Playlist:
    def __init__(self):
        self.__items = []

    def download(self, sp: spotipy.client.Spotify, playlist_id: str) -> None:
        page_size = 100
        offset = 0
        fields = ','.join([
            'items.track.name',
            'items.track.artists.name',
            'items.added_by.id',
            'items.added_at',
        ])
        while True:
            rsp = sp.playlist_items(
                playlist_id,
                limit=page_size,
                offset=offset,
                fields=fields,
                additional_types=['track']
            )
            if not rsp['items']:
                break

            self.__items += [
                PlaylistItem(s['track']['name'], s['added_at'], s['added_by']['id'], s['track']['artists']) 
                for s in rsp['items'] if s['track']
            ]
            offset += page_size

    def duplicates(self, key: str) -> list[PlaylistItem]:
        rgx = re.compile(key)
        items = []
        for item in self.__items:
            g = re.fullmatch(rgx, item.key())
            if g:
                items.append((g.groups(), item))

        items.sort(key = itemgetter(0))
        grp = groupby(items, key = itemgetter(0))
        dups = []
        for _, v in grp:
            lv = list(v)
            if len(lv) > 1:
                dups += [item[1] for item in lv]
        return dups


def write_to_csv(filename: str, items: list[PlaylistItem]) -> None:
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=vars(items[0]).keys())
        writer.writeheader()
        for item in items:
            writer.writerow(vars(item))

def main(args: str) -> None:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    playlist_id = args[1]

    playlist = Playlist()
    playlist.download(sp, playlist_id)
    duplicates = playlist.duplicates(args[2])
    write_to_csv("duplicates.csv", duplicates)


if __name__ == "__main__":
    main(sys.argv)
