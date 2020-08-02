import praw
import config
import re
import tempfile
import subprocess
import prawcore
import os

# Usage: Before running this program, you need to rename `config-template.py` to `config.py` and change the values inside the file to your reddit api credentials.
# You also should update the global configuration values to reflect your usecase.
# In order to use the script, just run it, and it should prompt you at the critical points.

# Dependencies:
#   vim

# Global configuration
# You probably should edit these
rootWikiPage = "mk6"
subreddit = "democraciv"
markToArchive = "mk6"
overwriteMessage = "This page will be filled once Mark VII starts."

# Global configuration
# Probably don't need to edit
linkRe = re.compile(r"\*?\+?\-? ?\[(.+)\]\((https?:\/\/[\w\d.\/?=#-]+)\)")
pageList = []
reddit = praw.Reddit(client_id=config.scriptId, client_secret=config.secret,
                     password=config.password, user_agent="USERAGENT",
                     username=config.username)

class Page():
    newContent = ""
    content = ""
    name = "test"
    page = "test"
    newname = "test"
    oldUrl = ""
    newUrl = ""
    def __init__ (self, page, rootpage=False):
        self.page = reddit.subreddit(subreddit).wiki[page]
        self.content = self.page.content_md
        self.oldUrl = "https://www.reddit.com/r/"+subreddit+"/wiki/" + page
        newWikiPageMatch = re.match(r'(https:\/\/www.reddit.com\/r\/'+subreddit+'\/wiki\/)(.*)', self.oldUrl)
        if not rootpage:
            self.newUrl = newWikiPageMatch.group(1) + markToArchive + "-" + newWikiPageMatch.group(2).replace('/','-')
            self.newname = markToArchive + "-" + newWikiPageMatch.group(2).replace('/','-')
        else:
            self.newUrl = self.oldUrl
            self.newname = page
    def links(self):
        return linkRe.findall(self.content)
    def updateContent(self,pageList):
        if self.newContent == "":
            self.newContent = self.content
        for i in pageList:
            self.newContent = self.newContent.replace("("+i.oldUrl+")", "("+i.newUrl+")")

def archivePage(page, rootpage=False):
    print("Archiving page:",page)
    currentPage = Page(page,rootpage=rootpage)
    pageList.append(currentPage)
    for match in currentPage.links():
        endPageMatch = re.match(r'(https:\/\/www.reddit.com\/r\/'+subreddit+'\/wiki\/)(.*)', match[1])
        alreadyMarked = False
        for i in pageList:
            if match[1] == i.oldUrl:
                alreadyMarked = True
        if "reddit.com/r/"+subreddit+"/wiki" not in match[1] or alreadyMarked:
            continue
        archive = input("Would you like to archive " + match[1] + " ? (y/n)")
        if archive == 'y':
            archivePage(endPageMatch.group(2))

archivePage(rootWikiPage, rootpage=True)
for page in pageList:
    page.updateContent(pageList)

for page in pageList:
    with tempfile.NamedTemporaryFile(suffix=".tmp") as oldContent, tempfile.NamedTemporaryFile(suffix=".tmp") as newContent:
        oldContent.write(page.content.encode()) 
        newContent.write(page.newContent.encode()) 
        oldContent.flush()
        newContent.flush()
        subprocess.call(["vim", "-d", oldContent.name, newContent.name])
        overwrite = input("Update wiki page with new content at " + page.newUrl + " ? (Y/n)")
        if overwrite == "Y":
            if not os.path.exists('backup'):
                os.makedirs('backup')
            with open("backup/" + page.page.name + ".md", 'w+') as backupfile:
                backupfile.write(page.content)
            try:
                test = reddit.subreddit(subreddit).wiki[page.newname].name
                print(test)
            except prawcore.exceptions.NotFound:
                print("Creating page with name", page.newname)
                reddit.subreddit(subreddit).wiki.create(page.newname, newContent, reason="Archiving old Wiki Pages")
            else:
                print("Modifying page with name", page.newname)
                reddit.subreddit(subreddit).wiki[page.newname].edit(content=page.newContent, reason="Archiving old Wiki Pages")
            replaceOldText = input("Replace the text of the page with the end of mark message? (Y/n) ")
            if replaceOldText == "Y":
                print("Modifying page with name", page.page.name)
                reddit.subreddit(subreddit).wiki[page.page.name].edit(content=overwriteMessage, reason="End of mark")
