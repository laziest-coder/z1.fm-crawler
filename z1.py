import requests
from bs4 import BeautifulSoup as bs
from pprint import pprint
import mysql.connector


base_url = "https://z1.fm/"

session = requests.session()
session.headers.update({'user-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36', 'Accept': '*/*', 'Connection': 'keep-alive', 'origin': 'https://z1.fm'})

def get_letters(base_url):
    index = session.get(base_url)

    if(index.status_code != 200):
        pass

    parsed = bs(index.text,"lxml")
    letters = parsed.select("div.edit-letter-spacing a")

    for letter in letters:
        yield base_url+letter.get("href")


def get_artists_list(letter_url):
    html = session.get(letter_url)
    parsed = bs(html.text,"lxml")
    artists = parsed.select("div.songs-list-item div.song-wrap-xl div.song-xl a.song-play")

    for artist in artists:
        image = artist.select_one("div.song-img img.lazy")
        yield {
            "image" : image.get("data-original"),
            "artist_url" : artist.get("href")
        }


def get_artist_songs(artist_url):
    html = session.get(artist_url)
    parsed = bs(html.text,"lxml")
    songs = parsed.select("div.songs-list-item div.song-wrap-xl div.song-xl")

    for song in songs:
        yield {
            "artist_name" : song.select_one("div.song-content div.song-artist a").text.strip(),
            "song_name" : song.select_one("div.song-content div.song-name a").text.strip(),
            "song_url" : "/download/"+song.get("data-play")
        }

# pprint(get_artist_songs("https://z1.fm/artist/3182575?sort=view&page=81"))

def add_song(artist,song_name,image,source,base):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="mysql",
        database="MusicSpider"
    )

    mycursor = mydb.cursor()

    sql = "INSERT INTO z1fm (artist,song_name,image,source,base) VALUES (%s,%s,%s,%s,%s)"
    val = (artist,song_name,image,source,base)
    mycursor.execute(sql,val)
    mydb.commit()
    print(" --> 1 record inserted, ID:", mycursor.lastrowid) 
    mycursor.close()

# pprint(get_artist_songs("https://z1.fm/artist/1861?sort=views&page=2"))

def crawl(base_url):

    letters = get_letters(base_url)
    for letter in letters:
        print("Letter url: "+letter)
        i = 1
        check = True
        while(check):
            letter_url = letter + "?page=" + str(i)
            print("Letter page: "+str(i))
            if(requests.get(letter_url).status_code != 200):
                break
            letter_artists = get_artists_list(letter_url)
            for artist in letter_artists:
                j = 1
                checkIn = True
                while(checkIn):
                    artist_url = base_url + artist["artist_url"] + "?sort=view&page=" + str(j)
                    artist_html = session.get(artist_url)
                    if(artist_html.status_code != 200):
                        break
                    artist_parsed = bs(artist_html.text,"lxml")
                    is_disabled = artist_parsed.select_one("div.paging")
                    artist_songs = artist_parsed.select("div.songs-list-item div.song-wrap-xl div.song-xl")
                    if not artist_songs:
                        break
                    songs = get_artist_songs(artist_url)
                    for song in songs:
                        add_song(song["artist_name"],song["song_name"],artist["image"],song["song_url"],artist_url)
                    if(is_disabled is None):
                        break
                    if(is_disabled.select_one("a.next.disabled") is not None):
                            break 
                    j = j + 1
                # break # 1 artist
            i = i + 1   
            # break # 1 artist page
        break # 1 letter        


pprint(crawl(base_url))
