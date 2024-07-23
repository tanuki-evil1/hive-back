import base64
import os
from functools import wraps
from ldap3 import Server, Connection, ALL, SUBTREE, NTLM, ENCRYPT
from ldap3.core.exceptions import LDAPBindError, LDAPCursorAttributeError, LDAPSocketReceiveError, LDAPSocketOpenError
import socket
from dns.resolver import Resolver
from setup_exch_cert import filter_certificates, get_certificate, save_certificate


GLOBAL_ADDRESS_LIST_ENTRIES = [
    'по умолчанию',
    'default'
]


def connect_to_ldap(func):
    @wraps(func)
    def wrapper(service, username, password, *args, **kwargs):
        if '@' not in username:
            conn_username = f'{service.domain_suffix}\\{username}'
        else:
            username, domain = username.split('@')
            conn_username = f'{service.domain_suffix}\\{username}'
            user_address_domain = str(service.get_user_email(username, password)).split('@')[-1]
            if domain.lower() not in [user_address_domain.lower(), service.domain_suffix.lower()]:
                raise Exception('Invalid domain name in username')
        try:
            conn = service.connection(
                    service.server,
                    conn_username,
                    password,
                    authentication=NTLM,
                    session_security=ENCRYPT,
            )
            conn.bind()
            result = func(service, conn, username, password, *args, **kwargs)
            conn.unbind()
            return result
        except (LDAPBindError, LDAPSocketReceiveError) as error:
            raise Exception(f'{repr(error)}. Check username and password')
        except LDAPSocketOpenError as error:
            raise Exception(f'{repr(error)}. Check AD config and availability')
    return wrapper


class ActiveDirectory:
    def __init__(self, ad_dns_name):
        self.server = Server(f"{ad_dns_name}", get_info=ALL)
        self.connection = Connection
        with self.connection(self.server):
            self.dns_server = socket.gethostbyname(self.server.info.other.get('dnsHostName')[0])
            self.dns_resolver = Resolver()
            self.dns_resolver.nameserver = self.dns_server
            self.netbios_name = self.server.info.other.get('ldapServiceName')[0].split('.')[0].upper()
            self.adsi_root = self.server.info.other.get('rootDomainNamingContext')[0]
            self.domain_suffix = self.adsi_root.replace('DC=', '').replace(',', '.')
            self.adsi_config_context = 'CN=Configuration,' + self.adsi_root

    @connect_to_ldap
    def get_domain_controllers(self, *args):
        conn, *_ = args
        conn.search(search_base=f'{self.adsi_root}',
                    search_filter='(&(objectCategory=computer)(userAccountControl:1.2.840.113556.1.4.803:=8192))',
                    search_scope=SUBTREE,
                    attributes=['dNSHostName']
                    )
        domain_controllers = []
        for domain_controller in conn.entries:
            try:
                defined_ip = str(self.dns_resolver.resolve(str(domain_controller.dNSHostName))[0])
            except socket.gaierror:
                defined_ip = None
            domain_controllers.append({
                'dc_name': str(domain_controller.dNSHostName),
                'dc_ip:': defined_ip
            })
        return domain_controllers

    @connect_to_ldap
    def get_user_base_data(self, *args):
        conn, username, *_ = args
        conn.search(search_base=f'{self.adsi_root}',
                    search_filter=f'(sAMAccountName={username})',
                    attributes=['sAMAccountName', 'givenName', 'sn', 'mail'])
        if len(conn.entries) == 1:
            entry = conn.entries[0]
            return {
                'first_name': str(entry.givenName),
                'last_name': str(entry.sn),
                'email': str(entry.mail),
                'username': str(entry.sAMAccountName)
            }

    @connect_to_ldap
    def search_user_data(self, *args, search_request):
        conn, *_, = args
        search_pattern = f'*{search_request}*' if search_request else '*'
        search_pattern = search_pattern if "@" in search_pattern else f'*{search_pattern}@*'
        conn.search(search_base=f'{self.adsi_root}',
                    search_filter=f'(&(|(mail={search_pattern})(displayName={search_pattern}))'
                                  f'(objectClass=person)(!(msExchHideFromAddressLists=TRUE)))',
                    attributes=['sAMAccountName', 'givenName', 'sn', 'mail'])
        result = []
        if conn.entries:
            for entry in conn.entries:
                result.append({
                    'first_name': str(entry.givenName),
                    'last_name': str(entry.sn),
                    'email': str(entry.mail),
                    'username': str(entry.sAMAccountName)
                })
        return result

    @connect_to_ldap
    def get_user_exchange_server(self, *args):
        conn, username, *_ = args
        conn.search(
            search_base=self.adsi_root,
            search_filter=f'(sAMAccountName={username})',
            attributes=['msExchHomeServerName']
        )
        user_exchange_server = {}
        for entry in conn.entries:
            try:
                user_exchange_server_name = str(entry.msExchHomeServerName).split('=')[-1]
            except LDAPCursorAttributeError:
                user_exchange_server_name = None
            if user_exchange_server_name:
                conn.search(
                    search_base=self.adsi_root,
                    search_filter=f'(name={user_exchange_server_name})',
                    attributes=['dNSHostName']
                )
                for exchange_server in conn.entries:
                    try:
                        exchange_server_ip = str(self.dns_resolver.resolve(str(exchange_server.dNSHostName))[0])
                    except socket.gaierror:
                        exchange_server_ip = None
                    user_exchange_server = {
                        'ms_exchange_name': str(exchange_server.dNSHostName),
                        'ms_exchange_ip': exchange_server_ip
                    }
        return user_exchange_server

    @connect_to_ldap
    def get_user_email(self, *args):
        conn, username, *_ = args
        conn.search(
            search_base=self.adsi_root,
            search_filter=f'(&(objectClass=person)(sAMAccountName={username}))',
            attributes=['mail']
        )
        return str(conn.entries[0].mail) or None

    @connect_to_ldap
    def get_default_gal(self, *args):
        conn, *_ = args
        conn.search(
            search_base=f'CN=Microsoft Exchange,CN=Services,CN=Configuration,{self.adsi_root}',
            search_filter='(&(objectClass=addressBookContainer)(cn=All Global Address Lists))',
        )
        address_lists_location = conn.entries[0].entry_dn
        conn.search(
            search_base=address_lists_location,
            search_filter='(objectClass=*)',
        )
        all_global_address_lists = conn.entries
        default_global_address_lists = [
            address_list.entry_dn for address_list in all_global_address_lists if
            any(str(entry) in str(address_list) for entry in GLOBAL_ADDRESS_LIST_ENTRIES)
        ]
        result_list = []
        if len(default_global_address_lists) == 1:
            gal = default_global_address_lists[0]
            conn.search(
                search_base=self.adsi_root,
                search_filter=f'(&(mailNickname=*)(showInAddressBook={gal})(objectClass=person)'
                              f'(!(userAccountControl=66050))(!(userAccountControl=514)))',
                attributes=['sAMAccountName', 'givenName', 'sn', 'mail']
            )
            for entry in conn.entries:
                result_list.append(
                    {
                        'first_name': str(entry.givenName),
                        'last_name': str(entry.sn),
                        'email': str(entry.mail),
                        'username': str(entry.sAMAccountName)
                    }
                )
            result_list = sorted(result_list, key=lambda x: x['username'])
        return result_list

    @connect_to_ldap
    def get_all_exchange_servers(self, *args):
        conn, *_ = args
        conn.search(
            search_base=self.adsi_config_context,
            search_filter='(objectClass=msExchExchangeServer)',
            attributes=['name']
        )
        result = []
        for exchange_server_entry in conn.entries:
            conn.search(
                search_base=self.adsi_root,
                search_filter=f'(name={exchange_server_entry.name})',
                attributes=['dNSHostName']
            )
            for exchange_server in conn.entries:
                try:
                    exchange_server_ip = str(self.dns_resolver.resolve(str(exchange_server.dNSHostName))[0])
                except socket.gaierror:
                    exchange_server_ip = None
                result.append({
                    'ms_exchange_name': str(exchange_server.dNSHostName),
                    'ms_exchange_ip': exchange_server_ip
                })
        return result

    @connect_to_ldap
    def get_root_ca_certificate(self, *args):
        conn, username, password, *_ = args
        conn.search(
            search_base=f'CN=Certification Authorities,CN=Public Key Services,CN=Services,{self.adsi_config_context}',
            search_filter='(objectClass=certificationAuthority)',
            attributes=['cACertificate']
        )
        all_certs = [cert for entry in conn.entries for cert in entry.cACertificate.values]
        cert_folder = 'certificates'

        created_files = []
        index = 0
        for cert in all_certs:
            file_name = f'domain_ca_{index}.cer'
            while os.path.exists(f'{cert_folder}/{file_name}'):
                index += 1
                file_name = f'domain_ca_{index}.cer'
            cert_data = base64.b64encode(cert).decode('utf-8')
            created_files.append(file_name)
            with open(f'{cert_folder}/{file_name}', 'w') as cert_file:
                cert_file.write('-----BEGIN CERTIFICATE-----\n')
                cert_file.write(cert_data)
                cert_file.write('\n-----END CERTIFICATE-----\n')
        root_certs = filter_certificates(cert_folder, self.domain_suffix.lower(), certs_to_process=created_files)
        if not root_certs:
            root_certs = []
            self_signed_collection = []
            exchange_servers = self.get_all_exchange_servers(username, password)
            for exchange_server in exchange_servers:
                exchange_server_cert = get_certificate(exchange_server.get('ms_exchange_ip'))
                self_signed_collection.append({
                    'ms_exchange_name': exchange_server.get('ms_exchange_name'),
                    'ms_exchange_ip': exchange_server.get('ms_exchange_ip'),
                    'ms_exchange_certificate': exchange_server_cert,
                })
            for self_signed_item in self_signed_collection:
                self_signed_cert = save_certificate(
                    cert=self_signed_item.get('ms_exchange_certificate'),
                    filename=self_signed_item.get('ms_exchange_name'),
                    folder=cert_folder
                )
                root_certs.append(self_signed_cert)
        return root_certs
