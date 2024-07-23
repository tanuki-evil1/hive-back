import os
from requests.adapters import HTTPAdapter
from exchangelib import Credentials, Account
from exchangelib import NTLM, Configuration
from urllib.parse import urlparse
import requests.adapters
from exchangelib.protocol import BaseProtocol
# from domain_controller import ActiveDirectory


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


# Надо думать
DOMAIN_NAME = ''

# Идея получать примерно так, но надо подумать:
# user.integrations.get(name='Active_directory').config.get('mailserver')
MAILSERVER = ''

# Идея получать по user.email
EMAIL = ''

# Идея получать примерно так, но надо подумать:
# user.integrations.get(name='Active_directory').config.get('ad_pwd')
PASSWORD = ''

credentials = Credentials(username=EMAIL, password=PASSWORD)
config = Configuration(
    credentials=credentials, auth_type=NTLM, server=MAILSERVER
)

account = Account(primary_smtp_address=EMAIL, credentials=credentials, config=config)
print(account)
