from datetime import datetime
import prompt
from exchangelib import Credentials, Account, CalendarItem, Q
from exchangelib import NTLM, Configuration
from exchangelib.items import SEND_TO_ALL_AND_SAVE_COPY
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
        exchange_server = active_directory.get_user_exchange_server(email, password).get('ms_exchange_ip')
        config = Configuration(credentials=credentials, auth_type=NTLM, server=exchange_server)
        super().__init__(primary_smtp_address=email, credentials=credentials, config=config)
        self.default_gal = active_directory.get_default_gal(username, password)

    def create_new_event(self):
        new_event = CalendarItem(
            account=self,
            folder=self.calendar,
            start=datetime(year=2024, day=12, month=7, hour=11, minute=30, tzinfo=self.default_timezone),
            end=datetime(year=2024, day=12, month=7, hour=14, minute=30, tzinfo=self.default_timezone),
            # Уведомление
            reminder_is_set=True,
            # Уведомить за указанное время до начала
            reminder_minutes_before_start=15,
            subject=prompt.string('Тема события: '),
            body=prompt.string('Описание события: '),
            # Список участников в виде списка адресов эл. почты
            required_attendees=[],
        )
        conflicting_events = self.calendar.filter(
            Q(start__lte=new_event.end) & Q(end__gte=new_event.start)
        )
        if conflicting_events.exists():
            print('Найдены конфликтующие события')
            for event in conflicting_events:
                print(
                    f'Конфликтное событие: {event.subject}, Начало: {event.start.strftime("%H:%M, %d.%m.%Y")}, Конец: {event.end.strftime("%H:%M, %d.%m.%Y")}')
            decision = prompt.string('Хотите создать событие несмотря на конфликты? (y/n): ')
            if decision == 'y':
                new_event.save(send_meeting_invitations=SEND_TO_ALL_AND_SAVE_COPY)
        else:
            decision = prompt.string('Хотите создать событие? (y/n): ')
            if decision == 'y':
                new_event.save(send_meeting_invitations=SEND_TO_ALL_AND_SAVE_COPY)


user = ExchangeAccount('hive.com', 'drlivsey', 'QwertY12345')
user.create_new_event()