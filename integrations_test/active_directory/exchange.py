from exchangelib import Credentials, Account
from exchangelib import NTLM, Configuration
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from domain_controller import ActiveDirectory
import urllib3


urllib3.disable_warnings()


# Use this adapter class instead of the default
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter


# Надо думать
# DOMAIN_NAME = ''
#
# # Идея получать примерно так, но надо подумать:
# # user.integrations.get(name='Active_directory').config.get('mailserver')
# MAILSERVER = ''
#
# # Идея получать по user.email
# EMAIL = ''
# print(EMAIL)
#
# # Идея получать примерно так, но надо подумать:
# # user.integrations.get(name='Active_directory').config.get('ad_pwd')
# PASSWORD = ''

# credentials = Credentials(username=EMAIL, password=PASSWORD)
# config = Configuration(
#     credentials=credentials, auth_type=NTLM, server=MAILSERVER
# )
# account = Account(primary_smtp_address=EMAIL, credentials=credentials, config=config)
# print(account.contacts)


class ExchangeAccount(Account):
    def __init__(self, domain_name, username, password):
        active_directory = ActiveDirectory(domain_name)
        email = active_directory.get_user_email(username, password)
        credentials = Credentials(username=email, password=password)
        server = active_directory.get_user_exchange_server(email, password).get('ms_exchange_ip')
        config = Configuration(credentials=credentials, auth_type=NTLM, server=server)
        super().__init__(primary_smtp_address=email, credentials=credentials, config=config)
        self.default_gal = active_directory.get_default_gal(username, password)
