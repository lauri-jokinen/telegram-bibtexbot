import os
import nextcloud_client # pyncclient
import json

with open("/home/lowpaw/Downloads/telegram-koodeja.json") as json_file:
  koodit = json.load(json_file)

path = '/home/lowpaw/Downloads/telegram-bibtexbot/notes'
notes_list = os.listdir(path)
notes_list.sort()

contents = []

for note_name in notes_list:
  fo = open(path + '/' + note_name, 'r')
  contents.append(fo.read())
  fo.close()

contents = '\n\n'.join(contents)

contents = contents.replace('\n* ', '\n\n* ') # helps with bullet point lists

fo = open('/home/lowpaw/Downloads/telegram-bibtexbot/notes.md', "w") # changed from .md to .tex
fo.write(contents)
fo.close()

os.system("pandoc /home/lowpaw/Downloads/telegram-bibtexbot/notes.md -o /home/lowpaw/Downloads/telegram-bibtexbot/notes.tex")
os.system("pdflatex /home/lowpaw/Downloads/telegram-bibtexbot/document.tex")

nc = nextcloud_client.Client('https://cloud.laurijokinen.com/nextcloud')
nc.login(koodit['NC_username'], koodit['NC_password'])
nc.put_file('Dokumentit/Notes/0document.pdf', '/home/lowpaw/Downloads/telegram-bibtexbot/document.pdf')
