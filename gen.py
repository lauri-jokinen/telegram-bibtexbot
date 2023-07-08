import os

path = '/home/lowpaw/Downloads/telegram-bibtexbot/notes'
notes_list = os.listdir(path)
notes_list.sort()

contents = []

for note_name in notes_list:
  fo = open(path + '/' + note_name, 'r')
  contents.append(fo.read())
  fo.close()

contents = '\n\n'.join(contents)

fo = open('/home/lowpaw/Downloads/telegram-bibtexbot/notes.md', "w")
fo.write(contents)
fo.close()

# html is generated with:
# https://www.makeuseof.com/md-block-render-markdown-web-page/

notes_html = ['''
<!DOCTYPE html>
<html lang="fi">
<meta>
<meta charset="utf-8">
</meta>
<body>
<style>"max-width:50px;"</style>
<md-block>
''','''
</md-block>
<style> md-block { width: 80px; font-family: "Trebuchet MS", sans-serif; } </style>
<script type="module" src="https://md-block.verou.me/md-block.js"></script>
</body>
</html>
'''
]

fo = open('/home/lowpaw/Downloads/telegram-bibtexbot/notes.html', "w")
fo.write(contents.join(notes_html))
fo.close()
