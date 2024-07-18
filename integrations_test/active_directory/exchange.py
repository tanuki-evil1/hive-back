import os
from datetime import datetime, timedelta
import ssl
from requests.adapters import HTTPAdapter
from exchangelib import Credentials, Account, DELEGATE, IMPERSONATION, CalendarItem, Q
from exchangelib import Build, NTLM, OAUTH2, BASIC, Configuration, Message, Mailbox
from exchangelib.version import Version
from urllib.parse import urlparse
import requests.adapters
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from dotenv import load_dotenv
from exchangelib.items import SEND_TO_ALL_AND_SAVE_COPY

