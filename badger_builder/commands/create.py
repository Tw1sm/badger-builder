from dotenv import load_dotenv
from pathlib import Path
from typing import List
import typer
import json
import copy

from badger_builder.logger import logger, init_logger
from badger_builder.lib.badgerbuilderai import BadgerBuilderAI
from badger_builder.lib.configs.listener import UserAgent, DataFormat, ObfSleep, get_ua_string
from badger_builder.lib import utils

app = typer.Typer()
COMMAND_NAME = 'create'
HELP = 'Generate a Brute Ratel C4 Profile with AI-assistance'


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main(
    # listener profile configurations
    jitter:         int         = typer.Option(40, '--jitter', help='Badger sleep jitter', rich_help_panel='Listener Configs'),
    sleep:          int         = typer.Option(60, '--sleep', help='Badger sleep interval', rich_help_panel='Listener Configs'),
    disable_ssl:    bool        = typer.Option(False, '--no-ssl', help='Disable listener SSL', rich_help_panel='Listener Configs'),
    comms_port:     int         = typer.Option(None, '--comms-port', help='If set, will generate a payload profile for the listener using the same configs but this port', rich_help_panel='Listener Configs'),
    bind_port:      int         = typer.Option(443, '--bind-port', help='Port the listener will bind to', rich_help_panel='Listener Configs'),
    bind_host:      str         = typer.Option(..., '--bind-host', help='Host the listener will bind to', rich_help_panel='Listener Configs'),
    hosts:          List[str]   = typer.Option(..., '--host', help='Add a rotational host for C2 communications (flag can be used multiple times)', rich_help_panel='Listener Configs'),
    response_type:  DataFormat  = typer.Option(..., '--resp-fmt', help='Data format to use for server HTTP response', rich_help_panel='Listener Configs', case_sensitive=False),
    request_type:   DataFormat  = typer.Option(..., '--req-fmt', help='Data format to use for client HTTP request', rich_help_panel='Listener Configs', case_sensitive=False),
    obfsleep:       ObfSleep    = typer.Option(..., '--obfsleep', help='Sleep obfuscation method', rich_help_panel='Listener Configs', case_sensitive=False),
    flavor:         str         = typer.Option(..., '--flavor', help='C2 communication flavor. Used to theme OpenAI queries for URIs, headers, HTTP requests', rich_help_panel='Listener Configs'),
    stomp:          str         = typer.Option(None, '--stomp', help='Module stomp a DLL', rich_help_panel='Listener Configs'),
    user_agent:     UserAgent   = typer.Option(..., '--user-agent', help='User-agent to use in comms to the listener', rich_help_panel='Listener Configs', case_sensitive=False),
    host_header:    str         = typer.Option(None, '--host-header', help='The Host header to use for HTTP requests', rich_help_panel='Listener Configs'),
    auth_count:     int         = typer.Option(1, '--auth-count', help='Number of authentication keys', rich_help_panel='Listener Configs'),
    ota:            bool        = typer.Option(False, '--ota', help='Enable one-time authentication', rich_help_panel='Listener Configs'),
    die:            bool        = typer.Option(False, '--die-offline', help='Kill the payload if internet is unavailable on lanuch', rich_help_panel='Listener Configs'),
    proxy:          str         = typer.Option(None, '--proxy', help='Proxy URL for payload connections', rich_help_panel='Listener Configs'),
    
    # operator configurations
    admins:         List[str]   = typer.Option(['admin'], '--admin', help='Add a commander admin (flag can be used multiple times)', rich_help_panel='Operator Configs'),
    operators:      List[str]   = typer.Option(None, '--operator', help='Add a commander operator (flag can be used multiple times)', rich_help_panel='Operator Configs'),
    
    # miscellaneous configurations
    no_autosave:    bool        = typer.Option(False, '--no-autosave', help='Disable profile autosave', rich_help_panel='Miscellaneous Configs'),
    cmd_host:       str         = typer.Option('0.0.0.0', '--cmd-host', help='Host the commander will bind to', rich_help_panel='Miscellaneous Configs'),
    cmd_port:       int         = typer.Option(8443, '--cmd-port', help='Port the commander will bind to', rich_help_panel='Miscellaneous Configs'),
    
    # autorun configurations
    killdate:       str         = typer.Option(None, '--kill-date', help='Badger kill date. Example: "30 Sep 21 22:55 IST"', rich_help_panel='Autorun Configs'),
    child:          str        = typer.Option(None, '--child', help='Set the child process spawned during fork and run', rich_help_panel='Autorun Configs'),
    malloc:         int        = typer.Option(None, '--malloc', help=utils.MALLOC_HELP, rich_help_panel='Autorun Configs'),
    threadexec:     int        = typer.Option(None, '--threadexec', help=utils.THREADEX_HELP, rich_help_panel='Autorun Configs'),

    # badger-builder options
    outfile:        Path        = typer.Option('profile.json', '--outfile', file_okay=True, writable=True, help='Output file for the profile', rich_help_panel='Badger Builder Options'),
    model:          str         = typer.Option('text-davinci-003', '--model', help='OpenAI model to interact with (chosen model may affect cost)',  rich_help_panel='Badger Builder Options'),
    temperature:    float       = typer.Option(1.2, '--temp', help='Temperature for OpenAI GPT-3 queries. Between 0.0 and 2.0. Higher values cause more randomness, while lower are more focused', rich_help_panel='Badger Builder Options'),
    debug:          bool        = typer.Option(False, '--debug', help='Enable debug logging', rich_help_panel='Badger Builder Options')
):      
    init_logger(debug)
    load_dotenv()

    logger.info('Badger is building your profile...')

    # validate autorun input first
    autoruns = []
    if killdate:
        if utils.validate_date(killdate):
            autoruns.append(f'set_killdate {killdate}')
        else:
            logger.error(f'Invalid killdate: {killdate}')
            raise typer.Exit(1)
        
    if bind_port == cmd_port:
        logger.error('Listener and commander bind ports cannot be the same')
        raise typer.Exit(1)
    
    if child:
        autoruns.append(f'set_child: {child}')

    if malloc:
        if utils.validate_malloc(malloc):
            autoruns.append(f'set_malloc {malloc}')
        else:
            logger.error(f'Invalid malloc value: {malloc}')
            raise typer.Exit(1)

    if threadexec:
        if utils.validate_threadexec(threadexec):
            autoruns.append(f'set_threadex {threadexec}')
        else:
            logger.error(f'Invalid threadexec value: {threadexec}')
            raise typer.Exit(1)

    # now we start building the profile JSON
    profile = {}

    # set operator configs
    profile['admin_list'] = {}
    for admin in admins:
        profile['admin_list'][admin] = utils.random_string(10)

    if operators:
        profile['user_list'] = {}
        for operator in operators:
            profile['user_list'][operator] = utils.random_string(10)


    # set misc configs
    profile["auto_save"] = not no_autosave
    profile['c2_handler'] = f'{cmd_host}:{cmd_port}'

    # set static ssl configs
    profile['ssl_cert'] = 'cert.pem'
    profile['ssl_key'] = 'key.pem'

    # create HTTP listener
    profile['listeners'] = {}
    profile['listeners']['http'] = {}
    listener =  profile['listeners']['http']

    # set static listener configs
    listener['is_random'] = False
    listener['os_type'] = 'windows'

    # set user-defined configs
    listener['host'] = bind_host
    listener['port'] = f'{bind_port}'
    listener['sleep'] = sleep
    listener['jitter'] = jitter
    listener['ssl'] = not disable_ssl
    listener['auth_type'] = ota
    listener['die_offline'] = die
    listener['useragent'] = get_ua_string(user_agent)
    listener['obfsleep'] = obfsleep.value
    listener['rotational_host'] = ','.join(hosts)

    listener['auth_count'] = auth_count
    listener['c2_authkeys'] = []
    for x in range(0, auth_count):
        listener['c2_authkeys'].append(utils.random_string(15))

    if proxy:
        listener['proxy'] = proxy

    if stomp:
        listener['stomp'] = stomp

    # get ChatGPT's input for dynamic configs
    logger.info(f'Querying OpenAI for "{flavor}" flavored listener configs...')
    badger_ai = BadgerBuilderAI(flavor, temperature, model)
    
    listener['c2_uri'] = badger_ai.uri_query()
    
    # Open AI gives bad JSON frequently, so we'll be safe
    # get client-side request headers
    while True:
        try:
            listener['request_headers'] = json.loads(
                badger_ai.http_header_query(
                    send_fmt=request_type.value,
                    recv_fmt=response_type.value, 
                    client_side=True
                )
            )
        except Exception:
            logger.error('OpenAI returned malformed JSON... retrying')
        else:
            break

    # remove user-agent and host header if supplied by OpenAI
    for header in listener['request_headers'].copy().keys():
        if header.lower() in ['user-agent', 'host']:
            del listener['request_headers'][header]
    
    if host_header:
        listener['request_headers']['host'] = host_header

    # get server-side response headers
    while True:
        try:
            listener['response_headers'] = json.loads(
                badger_ai.http_header_query(
                    send_fmt=response_type.value,
                    recv_fmt=request_type.value, 
                    client_side=False
                )
            )
        except Exception:
            logger.error('OpenAI returned malformed JSON... retrying')
        else:
            break
    

    # get client-side request body
    body = ''
    while True:
        body = badger_ai.http_body_query(request_type.value, client_side=True)
        if 'DataBlobPlaceholder' in body and body.count('DataBlobPlaceholder') == 1:
            break
        else:
            logger.error('OpenAI returned malformed HTTP request body... retrying')

    request = body.split('DataBlobPlaceholder', 1)
    listener['prepend'] = request[0]
    listener['append'] = request[1]
    

    # get server-side response body
    while True:
        body = badger_ai.http_body_query(response_type.value, client_side=False)
        if 'DataBlobPlaceholder' in body and body.count('DataBlobPlaceholder') == 1:
            break
        else:
            logger.error('OpenAI returned malformed HTTP response body... retrying')

    response = body.split('DataBlobPlaceholder', 1)
    listener['prepend_response'] = response[0]
    listener['append_response'] = response[1]


    # get empty server response
    listener['empty_response'] = badger_ai.empty_resp_query(response_type.value)

    # setup payload profile, if necessary
    if comms_port and comms_port != bind_port:
        logger.info('Comms port is defined and is different from bind port - creating corresponding payload profile... ')
        profile['payload_config'] = {}

        # copy listener configs to payload profile
        profile['payload_config']['http-custom'] = copy.deepcopy(listener)
        profile['payload_config']['http-custom']['type'] = 'HTTP'

        # change port to comms port
        profile['payload_config']['http-custom']['port'] = f'{comms_port}'

        # remove c2_authkeys list and replace with a single val from the list
        del profile['payload_config']['http-custom']['c2_authkeys']
        profile['payload_config']['http-custom']['c2_auth'] = listener['c2_authkeys'][0]


    if len(autoruns) > 0:
        profile['autoruns'] = autoruns

    # dump to file!
    with open (outfile, 'w') as f:
       f.write(json.dumps(profile, indent=4))
    
    logger.info(f'Profile saved to {outfile}')

    # print HTTP traffic
    logger.info(f'Run \'badger-builder parse {outfile}\' to see sample HTTP traffic')
