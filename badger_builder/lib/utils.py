import random
from datetime import datetime
from base64 import b64encode

from badger_builder.logger import console

THREADEX_HELP = '''
Change thread execution technique. Options:\n
[0]  - CreateRemoteThread (WINAPI)\n
[1]  - RtlCreateUserThread (NTAPI)\n
[2]  - NtCreateThreadEx (NTAPI)\n
[3]  - QueueUserAPC, ResumeThread (WINAPI)\n
[4]  - QueueUserAPC, NtResumeThread (WINAPI+NTAPI)\n
[5]  - QueueUserAPC, NtAlertResumeThread (WINAPI+NTAPI)\n
[6]  - NtQueueApcThread, ResumeThread (NTAPI+WINAPI)\n
[7]  - NtQueueApcThread, NtResumeThread (NTAPI)\n
[8]  - NtQueueApcThread, NtAlertResumeThread (NTAPI)\n
[9]  - NtCreateThreadEx (Obfuscated Indirect Syscalls - x64 only\n
[10] - NtQueueApcThread, NtResumeThread (Obfuscated Indirect Syscalls - x64 only)\n
[11] - NtQueueApcThread, NtAlertResumeThread (Obfuscated Indirect Syscalls - x64 only)\n
[12] - Remote Procedure Call
'''

MALLOC_HELP = '''
Change memory allocation technique. Options:\n
[0] - VirtualAllocEx, VirtualProtectEx, WriteProcessMemory (WINAPI)\n
[1] - NtCreateSection, NtMapViewOfSection, RtlCopyMemory (NTAPI)\n
[2] - NtAllocateVirtualMemory, NtProtectVirtualMemory, NtWriteVirtualMemory (NTAPI)\n
[3] - NtCreateSection, NtMapViewOfSection, RtlCopyMemory (Obfuscated Indirect Syscalls - x64 only)\n
[4] - NtAllocateVirtualMemory, NtProtectVirtualMemory, NtWriteVirtualMemory (Obfuscated Indirect Syscalls - x64 only)
'''

DEFAULT_CLIENT_HEADERS = {
    'Host': '',
    'Content-Length': '',
    'Cache-Control': 'no-cache',
}

DEFAULT_SERVER_HEADERS = {
    'Content-Type': 'text/html',
    'Date': '',
    'Content-Length': ''
}


def random_string(length):
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    return ''.join(random.choice(charset) for _ in range(length))


def validate_date(date_string):
    try:
        date_format = '%d %b %y %H:%M %Z'
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False
    

def validate_malloc(malloc):
    try:
        malloc = int(malloc)
        if malloc < 0 or malloc > 4:
            return False
        return True
    except ValueError:
        return False
    

def validate_threadexec(threadexec):
    try:
        threadexec = int(threadexec)
        if threadexec < 0 or threadexec > 12:
            return False
        return True
    except ValueError:
        return False
    

def print_traffic_profile(profile):
    sample_client_data = b64encode(random_string(256).encode()).decode()
    sample_server_data = b64encode(random_string(128).encode()).decode()
    
    DEFAULT_CLIENT_HEADERS['Content-Length'] = len(sample_client_data)
    DEFAULT_SERVER_HEADERS['Content-Length'] = len(sample_server_data)

    DEFAULT_SERVER_HEADERS['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # add profile headers to default headers
    for header, value in profile['listeners']['http']['request_headers'].items():
        # don't duplicate default headers. Brute will do this filtering
        # so it's fine to do here (vs in main profile logic)
        if header.lower() == 'cache-control':
            DEFAULT_CLIENT_HEADERS['Cache-Control'] = value
        elif header.lower() == 'content-length':
            DEFAULT_CLIENT_HEADERS['Content-Length'] = value
        elif header.lower() == 'host':
            DEFAULT_CLIENT_HEADERS['Host'] = value
        else:
            DEFAULT_CLIENT_HEADERS[header] = value

    if DEFAULT_CLIENT_HEADERS['Host'] == '':
        DEFAULT_CLIENT_HEADERS['Host'] = profile['listeners']['http']['rotational_host'].split(',')[0]
        
        port = profile['listeners']['http']['port']
        if 'payload_config' in profile.keys():
            port = profile['payload_config']['http-custom']['port']
        
        if port not in ['80', '443']:
            DEFAULT_CLIENT_HEADERS['Host'] += f':{port}'

    for header, value in profile['listeners']['http']['response_headers'].items():
        if header.lower() == 'content-length':
            DEFAULT_SERVER_HEADERS['Content-Length'] = value
        elif header.lower() == 'content-type':
            DEFAULT_SERVER_HEADERS['Content-Type'] = value
        elif header.lower() == 'date':
            DEFAULT_SERVER_HEADERS['Date'] = value
        else:
            DEFAULT_SERVER_HEADERS[header] = value

    uri = profile['listeners']['http']['c2_uri'][0]
    print()
    console.print(f'POST /{uri} HTTP/1.1', style='red on default', highlight=False)
    for header, value in DEFAULT_CLIENT_HEADERS.items():
        console.print(f'{header}: {value}', style='red on default', highlight=False)
    console.print()
    data = profile['listeners']['http']['prepend'] + sample_client_data + profile['listeners']['http']['append']
    console.print(data, style='red on default', highlight=False)
    
    print()

    console.print('HTTP/1.1 200 OK', style='blue on default', highlight=False)
    for header, value in DEFAULT_SERVER_HEADERS.items():
        console.print(f'{header}: {value}', style='blue on default', highlight=False)
    console.print()
    data = profile['listeners']['http']['prepend_response'] + sample_server_data + profile['listeners']['http']['append_response']
    console.print(data, style='blue on default', highlight=False)

    print()