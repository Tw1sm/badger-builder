import random
from datetime import datetime


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