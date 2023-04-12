from pathlib import Path
from base64 import b64encode
from datetime import datetime
import typer
import json
import copy

from badger_builder.logger import init_logger, console
from badger_builder.lib.utils import DEFAULT_CLIENT_HEADERS, DEFAULT_SERVER_HEADERS, random_string

app = typer.Typer()
COMMAND_NAME = 'parse'
HELP = 'Print a sample BRc4 HTTP request and response using profile configs'


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main(
    profile: Path = typer.Argument(..., help='Path to the JSON profile to parse', exists=True, file_okay=True, dir_okay=False, readable=True),
):
    init_logger(False)

    with open(profile, 'r') as f:
        json_profile = json.load(f)

    for name, profile in json_profile['listeners'].items():
        if 'dnshost' not in profile.keys():
            console.rule(f'[bold yellow]Listener: {name}')
            print_profile(profile)

    if 'payload_config' in json_profile.keys():
        for name, profile in json_profile['payload_config'].items():
            if profile['type'].upper() == 'HTTP':
                console.rule(f'[bold yellow]Payload Profile: {name}')
                print_profile(profile)


def print_profile(profile):
    sample_client_data = b64encode(random_string(128).encode()).decode()
    sample_server_data = b64encode(random_string(64).encode()).decode()

    client_headers = copy.deepcopy(DEFAULT_CLIENT_HEADERS)
    server_headers = copy.deepcopy(DEFAULT_SERVER_HEADERS)
    empty_headers = copy.deepcopy(DEFAULT_SERVER_HEADERS)
    
    server_headers['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    empty_headers['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    if 'useragent' in profile.keys():
        client_headers['User-Agent'] = profile['useragent']

    # add profile headers to default headers
    if 'request_headers' in profile.keys():
        for header, value in profile['request_headers'].items():
            # don't duplicate default headers. Brute will do this filtering
            # so it's fine to do here (vs in main profile logic)
            if header.lower() == 'cache-control':
                client_headers['Cache-Control'] = value
            elif header.lower() == 'content-length':
                client_headers['Content-Length'] = value
            elif header.lower() == 'host':
                client_headers['Host'] = value
            else:
                client_headers[header] = value

    if client_headers['Host'] == '':
        client_headers['Host'] = profile['rotational_host'].split(',')[0]
                
        if profile['port'] not in ['80', '443']:
            client_headers['Host'] += f':{profile["port"]}'

    if 'response_headers' in profile.keys():
        for header, value in profile['response_headers'].items():
            if header.lower() == 'content-length':
                server_headers['Content-Length'] = value
            elif header.lower() == 'content-type':
                server_headers['Content-Type'] = value
            elif header.lower() == 'date':
                server_headers['Date'] = value
            else:
                server_headers[header] = value

    console.print('Badger request', style='bold yellow')
    uri = profile['c2_uri'][0]
    
    data = ''
    if 'prepend' in profile.keys():
        data += profile['prepend']
    data += sample_client_data
    if 'append' in profile.keys():
        data += profile['append']

    client_headers['Content-Length'] = str(len(data))
    console.print(f'POST /{uri} HTTP/1.1', style='red on default', highlight=False)
    for header, value in client_headers.items():
        console.print(f'{header}: {value}', style='red on default', highlight=False)
    print()
    console.print(data, style='red on default', highlight=False)
    
    print()
    console.print('Commander response', style='bold yellow')

    data = ''
    if 'prepend_response' in profile.keys():
        data += profile['prepend_response']
    data += sample_server_data
    if 'append_response' in profile.keys():
        data += profile['append_response']

    server_headers['Content-Length'] = str(len(data))
    console.print('HTTP/1.1 200 OK', style='blue on default', highlight=False)
    for header, value in server_headers.items():
        console.print(f'{header}: {value}', style='blue on default', highlight=False)
    print()
    console.print(data, style='blue on default', highlight=False)

    print()
    console.print('Commander empty response', style='bold yellow')

    console.print('HTTP/1.1 200 OK', style='blue on default', highlight=False)
    default_resp = 'Page not found'
    if 'empty_response_headers' in profile.keys():
        empty_headers['Content-Length'] = str(len(profile['empty_response']))
    else:
        empty_headers['Content-Length'] = len(default_resp)

    for header, value in empty_headers.items():
        console.print(f'{header}: {value}', style='blue on default', highlight=False)

    print()
    if 'empty_response' in profile.keys():
        console.print(profile['empty_response'], style='blue on default', highlight=False)
    else:
        console.print(default_resp, style='blue on default', highlight=False)
    print()

