import os
from requests.adapters import HTTPAdapter
from exchangelib import Credentials, Account
from exchangelib import NTLM, Configuration
from urllib.parse import urlparse
import requests.adapters
from exchangelib.protocol import BaseProtocol


# Setup custom SSL cert
class RootCAAdapter(requests.adapters.HTTPAdapter):
    """An HTTP adapter that uses a custom root CA certificate at a hard coded
    location.
    """

    def cert_verify(self, conn, url, verify, cert):
        cert_file = {
            "": f"{os.path.dirname(__file__)}",
        }[urlparse(url).hostname]
        super().cert_verify(conn=conn, url=url, verify=cert_file, cert=cert)


# Use this adapter class instead of the default
BaseProtocol.HTTP_ADAPTER_CLS = RootCAAdapter


# Initial auth data
DOMAIN_NAME = ''
MAILSERVER = ''
EMAIL = ''
PASSWORD = ''
USERNAME = f"{DOMAIN_NAME}\\{EMAIL.split('@')[0]}"

credentials = Credentials(username=USERNAME, password=PASSWORD)
config = Configuration(
    credentials=credentials, auth_type=NTLM, server=MAILSERVER
)

account = Account(primary_smtp_address=EMAIL, credentials=credentials, config=config)
print(account)
