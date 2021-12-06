import boto3
import json
import os
import sys
import logging

import feedparser

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

SES_CLIENT = boto3.client("ses", region_name="us-east-1")

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def send_email(mime_msg, source, destinations, verified_sender_arn=None):
    response = SES_CLIENT.send_raw_email(
        RawMessage={"Data": mime_msg.as_string()},
        Source=source,
        Destinations=destinations,
        SourceArn=verified_sender_arn,
    )
    logger.debug(response)


def build_email(user_info, service_info):
    msg = MIMEMultipart()
    msg["Subject"] = "Your Weekly AWS Updates"
    msg["From"] = "{} <{}>".format(
        "AWS News Service", os.environ.get("SENDER_EMAIL", "sender@trek10.com")
    )
    msg["To"] = user_info.get("email")

    msg.preamble = (
        "We found a custom AWS news update based on your saved preferences.\n"
    )
    part = MIMEText(format_html_news(user_info["username"], service_info), "html")
    msg.attach(part)

    return msg


def get_weekly_news():
    data = feedparser.parse(os.environ.get("AWS_RSS_URL"))
    return data["entries"]


def get_service_data_for_user(user_services):
    raw_news = get_weekly_news()
    user_news = {}
    for entry in raw_news:
        tags = "".join([x["term"] for x in entry["tags"]]).split(",")
        for service in user_services:
            match = False
            for tag in tags:
                if "-{}".format(service) in tag:
                    match = True
                    break
            if match:
                if service in user_news:
                    user_news[service].append(entry)
                else:
                    user_news[service] = [entry]
                break
    return user_news


def format_html_news(username, raw_user_news):
    html = "<html><head></head><body>"
    html += "<h1>Your Weekly Updates</h1>"
    html += "<p>Hello {},<br>Here's a customized AWS product news update based on your saved preferences! You can edit your interests anytime via the What's New API.</p>".format(
        username
    )
    for service, items in raw_user_news.items():
        html += "<h2>{}</h2><ul>".format(service)
        for item in items:
            html += '<li><b><a href="{}">{}</a></b></li>'.format(
                item["links"][0]["href"], item["title"]
            )
            html += "{}".format(item["summary"])
            html += "</p><br>"
        html += "</ul>"
    html += "</body></html>"
    logger.info(html)
    return html


def lambda_handler(event, context):
    logger.info(event)
    user_data = event.get("detail")
    service_info = get_service_data_for_user(user_data["services"])
    if service_info:
        email_contents = build_email(user_data, service_info)
        send_email(
            email_contents,
            os.environ.get("SENDER_EMAIL", "sender@trek10.com"),
            [user_data["email"]],
            os.environ.get("VERIFIED_SENDER_ARN"),
        )
