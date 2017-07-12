# -*- coding: utf-8 -*-
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import time
import datetime

def sendEmail(subscriber, html):
    # me == my email address
    # you == recipient's email address
    me = "R.E. News Daily"
    you = subscriber

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "R.E. News Daily: {}".format(time.strftime("%d/%m/%Y"))
    msg['From'] = me
    msg['To'] = subscriber

    # Create the body of the message (a plain-text and an HTML version).
    text = "If you can see this, your email doesn't allow HTML. Sorry :("

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login('advertapibot@gmail.com', 'tulqshqdakaooszh')
    mail.sendmail(me, you, msg.as_string())
    mail.quit()

def getSubscribers():
    resource = boto3.resource('dynamodb',
            aws_access_key_id='AKIAJ7WOM4HRYLQBTO7Q',
            aws_secret_access_key='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',
            region_name='us-east-1')
    proxy_table = resource.Table('renews-subscribers')
    response = proxy_table.scan()
    print "Found these subscribers:"
    for name in response['Items']:
        print "...", name['uid']
    return [name['uid'] for name in response['Items']]

def getFeedList():
    resource = boto3.resource('dynamodb',
            aws_access_key_id='AKIAJ7WOM4HRYLQBTO7Q',
            aws_secret_access_key='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',
            region_name='us-east-1')
    proxy_table = resource.Table('renews-feeds')
    response = proxy_table.scan()
    feedList = []
    for feed in response['Items']:
        feedList.append({"url":feed['url'], "title":feed['title']})
    return feedList

def getFeedData(feed):
    feed = feedparser.parse(feed['url'])
    items = []
    channel_title = re.sub(u"\u2013", "-", feed['channel']['title'])
    for i in feed['items']:
        item_title = re.sub(u"\u2013", "-", i['title'])
        date = " ".join(i for i in i['published'].split(" ")[1:4])
        date = datetime.datetime.strptime(date, '%d %b %Y')
        today = datetime.datetime.today()
        if date >= today - datetime.timedelta(hours=36):
            items.append({"title": item_title,
                          "link": i['link'],
                          "date": date.strftime('%b %d')})
    return {"title":channel_title,
            "items":items}

def main(event, context):
    allFeedData = []
    html = """
    <html>
          <head></head>
          <body>
              <table style="width:100%, border-spacing:5px, padding:5px">

    """
    
    subscribers = getSubscribers()
    
    feedList = getFeedList()
    for feed in feedList:
        allFeedData.append(getFeedData(feed))

    #
    #   Time to make some HTML
    #

    #for each feed
    for feed in allFeedData:
        if len(feed['items']) >= 1:
            html += """<tr>
                            <td colspan="2"><strong><h3>{t}</h3></strong>
                            </td>
                        </tr>""".format(t=feed['title'])
            for entry in feed['items']:
                link = re.sub(u"\u2019", "", entry['link'])
                title = re.sub(u"\u2019", "", entry['title'])
                date = re.sub(u"\u2019", "", entry['date'])

                link = re.sub(u'\u2026', "...", link)
                title = re.sub(u'\u2026', "...", title)
                date = re.sub(u'\u2026', "...", date)

                link = re.sub(u'\u201c', '', link)
                title = re.sub(u'\u201c', '', title)
                date = re.sub(u'\u201c', '', date)

                link = re.sub(u'\u201d', '', link)
                title = re.sub(u'\u201d', '', title)
                date = re.sub(u'\u201d', '', date)

                link = re.sub(u'\u2014', '-', link)
                title = re.sub(u'\u2014', '-', title)
                date = re.sub(u'\u2014', '-', date)

                link = re.sub(u'\u2018', "'", link)
                title = re.sub(u'\u2018', "'", title)
                date = re.sub(u'\u2018', "'", date)

                html += """<tr>
                                <td><strong>
                                    <a href="{l}">{h}</a>
                                    </strong>
                                </td>
                                <td>{d}
                                </td>
                            </tr>""".format(l=link, h=title, d=date)
            html += """<tr></tr>"""
        else:
            html += """<tr>
                            <td colspan="2"><strong><h3>{t}</h3></strong>
                            </td>
                        </tr>
                        <tr>
                            <td>Nothing to report today...</td>
                        </tr>
                        """.format(t=feed['title'])
            
    html += """
              </table>
            </body>
        </html>"""

    #ready to send the email
    for person in subscribers:
        print "emailing:", person
        sendEmail(person, html)


if __name__ == "__main__":
    main("","")
