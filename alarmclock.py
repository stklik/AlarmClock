#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime # DateToTextConverter
import urllib2, json # Weather
import feedparser # BBC news

import textwrap, subprocess, urllib2 # for downloading
    
class DateToTextConverter:
    
    def __init__(self, date = None ):
        if(date==None):
            self.date = datetime.datetime.now()#date.today()
        else:
            self.date = date
    
    def getPeriod(self):
        if(self.date.hour < 12):
            return "morning"
        elif(self.date.hour < 17):
            return "afternoon"
        else:
            return "evening"
    
    def getTimeAsText(self):
        return self.date.strftime("%I:%M %p")
    
    def getDateAsText(self):
        return "%s, the %s of %s" % (self.getWeekdayAsText(), self.getDayAsText(), self.getMonthAsText()) 
        
    def getWeekdayAsText(self):
        return self.date.strftime("%A")
        
    def getMonthAsText(self):
        return self.date.strftime("%B")
        
    def getDayAsText(self):
        day = self.date.day
        if(day % 10 == 1 and day != 11):
            return str(day)+"st"
        elif(day % 10 == 2 and day != 12):
            return str(day)+"nd"
        elif(day % 10 == 3 and day != 13):
            return str(day)+"rd"
        else:
            return str(day)+"th"

class WeatherEngine:
    #http://api.openweathermap.org/data/2.5/weather?id=5125771&units=metric
    baseUrl = "http://api.openweathermap.org/data/2.5/"
    todayUrlPart = "weather"
    forecastUrlPart = "forecast/daily"

    def __init__(self):
        self.location = "Geneva,ch"
        self.fetchToday()
        self.fetchForecast()

    def getWeatherMessage(self):
        now = "The weather conditions are %s with a temperature of %d degrees." % (self.getConditions(), self.getTemperature())
        future = "The temperature will be between %s and %s degrees." % (round(self.getLowForecast()), round(self.getHighForecast()))
        return [now, future]

    def getConditions(self):
        return self.today['weather'][0]['description']
        
    def getTemperature(self):
        return self.today['main']['temp']
        
    def getLowForecast(self):
        return self.forecast['list'][0]['temp']['night']
        
    def getHighForecast(self):
        return self.forecast['list'][0]['temp']['day']

    def fetchToday(self):
        data = self._askForData(self.todayUrlPart)
        self.today = data

    def fetchForecast(self):
        data = self._askForData(self.forecastUrlPart)
        self.forecast = data

    def _askForData(self, when):
        try:
            weather_api = urllib2.urlopen(self._buildUrl(when))
            response = weather_api.read()
            response_dictionary = json.loads(response)
            return response_dictionary
        except urllib2.HTTPError, e:
            return 'Failed to connect to Open Weather Map. (1)  '
        except urllib2.URLError, e:
            return 'Failed to connect to Open Weather Map. (2)  '
        except Exception:
            return 'Failed to connect to Open Weather Map. (3)  '

    def _buildUrl(self, when):
        url =  self.baseUrl+when+"?q="+self.location+"&units=metric"
        return url

class BBCNews:
    rssUrls = [
#        ("Top", "http://feeds.bbci.co.uk/news/rss.xml"),
        ("World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Europe", "http://feeds.bbci.co.uk/news/world/europe/rss.xml"),
        ("Technology", "http://feeds.bbci.co.uk/news/technology/rss.xml")
        ]
    
    numberOfHeadlines = 5
    
    def getAllNews(self):
        news = []
        for (title, url) in self.rssUrls:
            news.append("Here are the BBC %s News:" % title)
            newsblock = self.getNews(url)
            news.extend(newsblock)
            
        return news
            
    def getNews(self, url):
        news = []
        rss = feedparser.parse(url)
        for index in range(self.numberOfHeadlines):
            news.append("%s." % rss.entries[index]['title'])
            news.append(rss.entries[index]['description'])
            
        return news

class Downloader:
    head = 'wget -q -U Mozilla '
    ttsUrl = 'http://translate.google.com/translate_tts?tl=en&q='
    output = '" -O ~/test/'
    tail = '.mp3 '
    
    def __init__(self, prefix="chunk_"):
        self.prefix = prefix
        
    def downloadMessages(self, messages):
        messages = self.cleanUpMessages(messages)
        # messages = self.changeSplits(messages)
        for idx,msg in enumerate(messages):
            self.convertToAudio(msg, str(idx))
        return len(messages) # return how many messages we should have...
        
    def changeSplits(self, messages):
        fulltext = " ".join(messages)
        chunks = textwrap.wrap(fulltext, 100)
        return chunks
        
    def cleanUpMessages(self, messages):
        newMessages = []
        for index,msg in enumerate(messages):
            newMessages.extend(self.cleanupMessage(msg))
        return messages
        
    def cleanupMessage(self, msg):
        msg = msg.replace('"', '').strip()
        msg = msg.replace("'", '').strip()
        return msg
        
    def convertToAudio(self, text, fileindex):
        try:
            file = self.prefix+fileindex
            sendthis = text.encode("utf-8").join(['"'+self.ttsUrl, self.output])
            call = self.head + sendthis +self.prefix + str(fileindex).zfill(2) + str(self.tail)
            print call
            print subprocess.check_output(call, shell=True)
        except subprocess.CalledProcessError:
            print "Problem with this text: ", text
            #print subprocess.check_output("echo " + text + " | festival --tts ", shell=True)




class AlarmClock:

    def __init__(self):
        self.name = "Stefan"
        self.dateHelper = DateToTextConverter()
        self.messageparts = []
        
    def readMessage(self):
        self.generateMessage()
        self.downloadSpeech()
        self.readSpeech()
        
    def generateMessage(self):
        self.greet()
        self.readDateAndTime()
        self.readWeatherInfo()
        self.readBBCNews()
        self.sayGoodbye()
    
    def greet(self):
        self.messageparts.append("Good %s, %s." % (self.dateHelper.getPeriod(), self.name))
    
    def readDateAndTime(self):
        self.messageparts.append("Today is %s. The time now is %s." % (self.dateHelper.getDateAsText(), self.dateHelper.getTimeAsText()))
    
    def readWeatherInfo(self):
        self.messageparts.extend(WeatherEngine().getWeatherMessage())
    
    def readBBCNews(self):
        self.messageparts.extend(BBCNews().getAllNews())
    
    def sayGoodbye(self):
        self.messageparts.append("This is all for now. Have a good day!")
    
    
    def downloadSpeech(self):
        Downloader("chunk_").downloadMessages(self.messageparts)
    
    def readSpeech(self):
        pass # TODO: implement me

        
if __name__ == "__main__":
    x = AlarmClock()
    x.readMessage()
