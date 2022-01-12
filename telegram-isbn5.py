#!/usr/bin/python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
import json
import isbnlib
from isbnlib.registry import bibformatters
from datetime import datetime
import datetime as d
import time
import math
import urllib
from tqdm import tqdm
from pyzbar import pyzbar
import argparse
import cv2

with open("/home/lowpaw/Downloads/telegram-koodeja.json") as json_file:
    koodit = json.load(json_file)

def info(update, context):
    update.message.reply_text("Welcome, this bot is used to find Finnish book meta information in BibTeX-form.\n--\n"
        "Tämä botti etsii ISBN-koodin avulla suomalaisen kirjan metatiedot BibTex-muodossa. "
        "Tiedot etsitään Finnan avoimen API:n kautta, joka on ehkä suurin suomalaisten kirjojen tietokanta. "
        "Tietokannassa saattaa olla vikoja, joten ethän luota tietoihin sokeasti. "
        "Lähetä kuva kirjan viivakoodista tai "
        "kirjoita ISBN-koodi botille suoraan ilman kenoviivakomentoa. Annetun koodin väliviivat eivät vaikuta botin toimintaan lainkaan. "
        "Botti toimii myös yleisenä viivakoodin ja QR-koodin lukijana. Samassa kuvassa saa olla useampi viivakoodi.\n\n"
        "Sähköpiikin tiedot perustuvat Fingridin käytönvalvontajärjestelmän reaaliaikaisiin mittauksiin. "
        "Tuotantovaje/tuotantoylijäämä kuvaa Suomen sähkön tuotannon ja kulutuksen välistä tasapainoa tuonnit ja viennit huomioon ottaen. "
        "Suomen tuotantovaje/tuotantoylijäämä lasketaan Suomen ja muiden Pohjoismaiden välisen sähkön nettotuonnin/nettoviennin ja kuluvalle tunnille sovitun tuonti/vientiohjelman erotuksena. Tieto päivittyy 3 minuutin välein.")
    
def feedback(update, context):
    feedback = update.message.text
    print(feedback)
    if feedback[9:] == "":
        update.message.reply_text('Kirjoita komennon jälkeen palautteesi')
    else:
        file = open('/home/lowpaw/Downloads/telegram-bibtexbot/isbn-palaute.txt', 'a')
        file.write("\n"+feedback[9:])
        update.message.reply_text('Kiitos palautteesta!')
        file.close()
  
def isbn2id(isbn):
    print(isbn)
    search = requests.get('https://api.finna.fi/v1/search?lookfor=' + isbn + '&field[]=isbns&field[]=id').json()  
    if search['resultCount'] == 0:
        bookID = False
    else:
        records = search['records']
        n = len(records)
        i = -1
        res = False
        recordIndex = -1
        separator = ","
        
        while res == False:
            i = i+1
            if i >= n+2:
                res = True
            try:
                isbnKandidaatti = separator.join(records[i]['isbns'])
                if isbn.replace('-','') in isbnKandidaatti.replace('-',''):
                    recordIndex = i
                    res = True
            except:
                res = res

        if recordIndex == -1:
            bookID = False
        else:
            bookID = records[recordIndex]['id']
    return bookID

def id2bibtex(bookID,isbn):
    finnaField = ['authors','title','year','edition','institutions','publishers']
    texField = ['      author','       title','        year','     edition','institutions','   publisher']
    
    recordURL = 'https://api.finna.fi/v1/record?id=' + bookID
    for i in range(0,len(finnaField)):
        recordURL = recordURL + '&field[]=' + finnaField[i]
    bookInfo = requests.get(recordURL).json()
    bookInfo = bookInfo['records'][0]
    
    print(bookInfo)
    bibTexCode = "@book{" + isbn +","
    jsonAuthors = bookInfo['authors']
    authors = formatAuthors2(jsonAuthors)
    print(list(bookInfo.keys()))
    
    for i in range(0,len(texField)):
        if finnaField[i] == 'authors':
            bibTexCode = bibTexCode + "\n "+ texField[i] +" = \"" + authors + "\","
        elif finnaField[i] in list(bookInfo.keys()):
            field = formatField(bookInfo[finnaField[i]])
            if field != False:
                if finnaField[i] == 'edition':
                    bibTexCode = bibTexCode + "\n "+ texField[i] +" = \"" + field.replace("p.","painos") + "\","
                else:
                    bibTexCode = bibTexCode + "\n "+ texField[i] +" = \"" + field + "\","
    bibTexCode = bibTexCode + "\n "+ "        isbn" +" = \"" + isbn + "\","
    bibTexCode = bibTexCode + "\n}"
    return bibTexCode
    
def formatAuthors(jsonAuthors):
    numberOfAuthors = len(list(jsonAuthors.values()))
    separator = ', '
    authors = ''
    for i in range(0,numberOfAuthors):
        if len(list(jsonAuthors.values())[i]) != 0:
            author = separator.join(list(list(jsonAuthors.values())[i].keys()))
            if i == 0:
                authors = author
            else:
                authors = authors + ' and ' + author
    return authors
    
def mergeAuthors(authors, author):
    name = author.split(', ')
    if authors == '':
        return name[1] + ' ' + name[0]
    else:
        return authors + ' and ' + name[1] + ' ' + name[0]
    
def formatAuthors2(jsonAuthors):
    authorTypes = list(jsonAuthors.keys())
    finalAuthors = ''
    for atype in authorTypes:
        if not (atype in ['corporate']):
            jsonAuthorList = jsonAuthors[atype]
            if not (jsonAuthorList == []):
                authorNames = list(jsonAuthorList.keys())
                for author in authorNames:
                    jsonAuthorInfo = jsonAuthorList[author]
                    if 'role' in list(jsonAuthorInfo.keys()):
                        if not jsonAuthorInfo['role'] == ['kääntäjä']:
                            finalAuthors = mergeAuthors(finalAuthors,author)
                    else:
                        finalAuthors = mergeAuthors(finalAuthors,author)
    return finalAuthors
            
    
def formatField(jsonField):
    if type(jsonField) == str:
        field = jsonField
    elif type(jsonField) == list:
        if len(jsonField)==1:
            newObject = jsonField[0]
            if type(newObject) == str:
                field = newObject
            else:
                field = False
    else:
        field = False
    return field


def find_isbn(update, context):
    isbn = update.message.text
    update.message.reply_text(isbn2bibtex(isbn))
    
def isbn2bibtex(isbn):
    if not (isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn)):
        bibTexCode = "Koodi ei ole ISBN-koodi :("     
    else:
        try:
            bookID = isbn2id(isbnlib.mask(isbn.replace('-','')))
        except:
            bookID = isbn2id(isbn.replace('-',''))
        if bookID == False:
            print('Kokeillaan googlea')
            bibTexCode = "Koodia ei löydy tietokannasta :("
            bibtex = bibformatters['bibtex']
            try:
                bibTexCode = bibtex(isbnlib.meta(isbn.replace('-',''),'goob'))
            except:
                bibTexCode = 'Kirjaa ei löydy Googlen eikä Finnan tietokannoista :('
        else:
            try:        
                bibTexCode = id2bibtex(bookID,isbnlib.mask(isbn.replace('-','')))
            except:
                bibTexCode = id2bibtex(bookID,isbn.replace('-',''))
    return bibTexCode

    
def tuoreinTieto():
    TOKEN = koodit["fingrid"] # lateus96
    # TOKEN = koodit["fingrid2"] lauri.a.jokinen
    five_minutes = d.timedelta(minutes=80)
    now = datetime.now() + five_minutes
    before = datetime.now() - five_minutes
    start = before.strftime("%Y-%m-%dT%HXXX%MXXX%S").replace('XXX','%3A') + '%2B' + "%02d" % math.floor(-time.timezone / 3600) + '%3A00'
    end = now.strftime("%Y-%m-%dT%HXXX%MXXX%S").replace('XXX','%3A') +'%2B' + "%02d" % math.floor(-time.timezone / 3600) + '%3A00'
    url2 = 'https://api.fingrid.fi/v1/variable/198/events/json?start_time=' + start + '&end_time=' + end
    return requests.get(url2, headers={'x-api-key': TOKEN, 'Accept': 'application/json'}).json()[-1]['value']

def spike(update, context):
    value = tuoreinTieto()
    if value < -100:
        update.message.reply_text('Verkossa on paljon alituotantoa (' + str(-value).replace('.',',') + ' MW). Kannattaa odottaa vartti ennen kuin laitat uunin päälle.')
    elif value < 0:
        update.message.reply_text('Verkossa on hieman alituotantoa (' + str(-value).replace('.',',') + ' MW)')
    elif value > 100:
        update.message.reply_text('Verkossa on paljon ylituotantoa (' + str(value).replace('.',',') + ' MW)')
    elif value > 0:
        update.message.reply_text('Verkossa on hieman ylituotantoa (' + str(value).replace('.',',') + ' MW)')
    elif value == 0:
        update.message.reply_text('Tuotanto on täydellisessä tasapainossa! (' + str(value).replace('.',',') + ' MW)')

def isbn_picture(update, context):
    update.message.reply_text("Ladataan kuvaa...")
    filepath = save_image(update)
    barcodes = read_barcode(filepath)
    if not barcodes:
        update.message.reply_text("En saanut kuvasta selvää :(")
    else:
        update.message.reply_text("Löysin seuraavat koodit:")
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
        update.message.reply_text(barcodeData)
        print(barcodeData)
        print(isbn2bibtex(barcodeData))
        update.message.reply_text(isbn2bibtex(barcodeData))

def save_image(update):
    file_id = update['message']['photo'][-1]['file_id']
    picLink = 'https://api.telegram.org/bot'
    picLink = picLink + koodit["isbn"]
    picLink = picLink + '/getFile?file_id='
    picLink = picLink + file_id
    file_path = requests.get(picLink).json()['result']['file_path']
    download_path = 'https://api.telegram.org/file/bot'
    download_path = download_path + koodit["isbn"]
    download_path = download_path + '/' + file_path
    
    response = requests.get(download_path)
    path = "/home/lowpaw/Nextcloud/Telegram-botit/isbn-to-bibtex/koodi.jpg"
    
    with open(path, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)
    return path
    
def read_barcode(path):
    image = cv2.imread("/home/lowpaw/Nextcloud/Telegram-botit/isbn-to-bibtex/koodi.jpg")
    # find the barcodes in the image and decode each of the barcodes
    barcodes = pyzbar.decode(image)
    return barcodes
    
def main():
  # Create Updater object and attach dispatcher to it
  updater = Updater(koodit["isbn"])
  dispatcher = updater.dispatcher
  print("Bibtexbot started")

  # Add command handler to dispatcher
  info_handler = CommandHandler('info',info)
  feedback_handler = CommandHandler('palaute',feedback)
  spike_handler = CommandHandler('piikki',spike)
  isbn_handler    = MessageHandler(Filters.text, find_isbn)
  picture_handler = MessageHandler(Filters.photo, isbn_picture)
  dispatcher.add_handler(info_handler)
  dispatcher.add_handler(feedback_handler)
  dispatcher.add_handler(spike_handler)
  dispatcher.add_handler(isbn_handler)
  dispatcher.add_handler(picture_handler)

  # Start the bot
  updater.start_polling()

  # Run the bot until you press Ctrl-C
  updater.idle()

if __name__ == '__main__':
  main()
