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
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            # Получаем сертификат
            cert = ssock.getpeercert(binary_form=True)
            return cert


def save_certificate(cert, filename, folder='certificates'):
    if not os.path.exists(folder):
        os.makedirs(folder)
    # Конвертируем бинарный сертификат в PEM формат
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
    pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
    file_path = os.path.join(folder, filename)
    # Сохраняем сертификат в файл
    with open(file_path, 'wb') as f:
        f.write(pem)


# # Пример использования
# host = 'exch-server'
# port = 443
# filename = f'{host}.cer'
#
# cert = get_certificate(host, port)
# save_certificate(cert, filename)
# print(f"Сертификат сохранен в {filename}")
