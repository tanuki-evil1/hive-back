from datetime import datetime, timezone
import ssl
import socket
import OpenSSL
import os


def get_certificate(host, port=443):
    # Создаем SSL контекст
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Подключаемся к серверу
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as secure_socket:
            # Получаем сертификат
            cert = secure_socket.getpeercert(binary_form=True)
            return cert


def save_certificate(cert, filename, folder='certificates'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    # Конвертируем бинарный сертификат в PEM формат
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
    pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
    file_path = f'{os.path.join(os.getcwd(), folder, filename)}.cer'
    print(file_path)
    # Сохраняем сертификат в файл
    with open(file_path, 'wb') as f:
        f.write(pem)
        return file_path


# # Пример использования
# host = 'hostname'
# port = 443
# filename = f'{host}'
#
# cert = get_certificate(host, port)
# save_certificate(cert, filename)
# print(f"Сертификат сохранен в {filename}")


# def filter_certificates(folder, domain_name=None, certs_to_process=None):
#     issuers_certs_data = {}
#     all_certs = [file for file in os.listdir(folder) if file.endswith(('.pem', '.cer'))]
#     for cert_file in sorted(all_certs):
#         with open(os.path.join(folder, cert_file), 'rb') as certificate:
#             certificate = certificate.read()
#             # Извлекаем данные сертификата
#             try:
#                 cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
#                 # Получаем время начала действия сертификата
#                 start_time_timestamp = cert.get_notBefore().decode('utf-8')
#                 # Переводим в datetime время начала действия
#                 start_time = datetime.strptime(start_time_timestamp, '%Y%m%d%H%M%S%z')
#                 if start_time > datetime.now(timezone.utc):
#                     continue
#                 # Получаем издателя
#                 issuer_raw = cert.get_issuer()
#                 # Пробуем преобразовать поле издателя в доменное имя
#                 issuer_fields = []
#                 for component in issuer_raw.get_components():
#                     issuer_fields.append(component[1].decode('utf-8').lower())
#                 # Если поля издателя извлеклись, то собираем доменное имя издателя
#                 # иначе преобразуем сырое значение в строку
#                 issuer = '.'.join(issuer_fields) if issuer_fields else str(issuer_raw)
#                 # Создаем описание текущего сертификата в виде словаря
#                 current_cert_data = {'start_time': start_time, 'cert_file': cert_file}
#
#                 # Проверяем уникальность сертификата издателя, где ключ - имя издателя
#                 # Если сертификат издателя есть, то оставляем тот, что более свежий
#                 # Если нет, то собираем в словарь с ключом [имя издателя] и значением - описанием сертификата
#                 if issuer in issuers_certs_data.keys():
#                     if current_cert_data['start_time'] > issuers_certs_data[issuer]['start_time']:
#                         issuers_certs_data[issuer] = current_cert_data
#                 else:
#                     issuers_certs_data[issuer] = current_cert_data
#
#             except Exception as e:
#                 print(f"Ошибка при обработке сертификата '{cert_file}': Description: {e}")
#                 continue
#     # Получаем список имён файлов для сертификатов из собранного словаря
#     valid_certs = [issuers_certs_data[issuer]['cert_file'] for issuer in issuers_certs_data]
#     # Если указано имя домена, то пробуем отфильтровать сертификаты по имени домена издателя
#     if domain_name:
#         domain_issuers = [issuer for issuer in issuers_certs_data.keys() if domain_name in issuer]
#         if domain_issuers:
#             valid_certs = [issuers_certs_data[issuer]['cert_file'] for issuer in domain_issuers]
#     # Формируем список невалидных сертификатов и удаляем
#     if certs_to_process:
#         certs_to_delete = [file for file in certs_to_process if file not in valid_certs]
#     else:
#         certs_to_delete = [file for file in all_certs if file not in valid_certs]
#     for cert_file in certs_to_delete:
#         os.remove(os.path.join(folder, cert_file))
#     filtered_certs = [os.path.join(os.getcwd(), folder, file) for file in os.listdir(folder) if file in valid_certs]
#     return filtered_certs


def get_all_cert_files(folder):
    return [file for file in os.listdir(folder) if file.endswith(('.pem', '.cer'))]


def load_certificate(cert_path):
    with open(cert_path, 'rb') as certificate_file:
        return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate_file.read())


def get_certificate_start_time(cert):
    start_time_str = cert.get_notBefore().decode('utf-8')
    return datetime.strptime(start_time_str, '%Y%m%d%H%M%S%z')


def get_certificate_issuer(cert):
    issuer_raw = cert.get_issuer()
    issuer_fields = [component[1].decode('utf-8').lower() for component in issuer_raw.get_components()]
    return '.'.join(issuer_fields) if issuer_fields else str(issuer_raw)


def is_valid_certificate(cert):
    start_time = get_certificate_start_time(cert)
    return start_time <= datetime.now(timezone.utc)


def filter_certificates_by_domain(valid_certs, issuers_certs_data, domain_name):
    return [
        issuers_certs_data[issuer]['cert_file']
        for issuer in issuers_certs_data
        if domain_name in issuer
    ] if domain_name else valid_certs


def delete_invalid_certificates(folder, certs_to_delete):
    for cert_file in certs_to_delete:
        os.remove(os.path.join(folder, cert_file))


def filter_certificates(folder: str, domain_name: str = None, certs_to_process: list = None) -> list:
    issuers_certs_data = {}
    all_certs = get_all_cert_files(folder)

    for cert_file in sorted(all_certs):
        cert_path = os.path.join(folder, cert_file)

        try:
            cert = load_certificate(cert_path)
            if not is_valid_certificate(cert):
                continue

            issuer = get_certificate_issuer(cert)
            start_time = get_certificate_start_time(cert)
            current_cert_data = {'start_time': start_time, 'cert_file': cert_file}

            if issuer in issuers_certs_data:
                if current_cert_data['start_time'] > issuers_certs_data[issuer]['start_time']:
                    issuers_certs_data[issuer] = current_cert_data
            else:
                issuers_certs_data[issuer] = current_cert_data

        except Exception as e:
            print(f"Ошибка при обработке сертификата '{cert_file}': {e}")
            continue

    valid_certs = [data['cert_file'] for data in issuers_certs_data.values()]
    valid_certs = filter_certificates_by_domain(valid_certs, issuers_certs_data, domain_name)

    certs_to_delete = [
        file for file in (certs_to_process if certs_to_process else all_certs)
        if file not in valid_certs
    ]

    delete_invalid_certificates(folder, certs_to_delete)

    filtered_certs = [
        os.path.join(os.getcwd(), folder, file)
        for file in os.listdir(folder)
        if file in valid_certs
    ]

    return filtered_certs
