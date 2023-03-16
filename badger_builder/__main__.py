from dotenv import load_dotenv
from pathlib import Path
from typing import List
import typer
import json

from badger_builder.logger import logger, init_logger
from badger_builder.lib.badgerbuilderai import BadgerBuilderAI
from badger_builder.lib.configs.listener import UserAgent, DataFormat, ObfSleep, get_ua_string
from badger_builder.lib import utils


app = typer.Typer(
    add_completion=False,
    rich_markup_mode='rich',
    context_settings={'help_option_names': ['-h', '--help']},
    pretty_exceptions_show_locals=False
)


@app.command(no_args_is_help=True, help='Create C4 Profiles')
def main(
    # listener profile configurations
    jitter:         int         = typer.Option(40, '--jitter', help='Badger sleep jitter', rich_help_panel='Listener Configs'),
    sleep:          int         = typer.Option(60, '--sleep', help='Badger sleep interval', rich_help_panel='Listener Configs'),
    disable_ssl:    bool        = typer.Option(False, '--no-ssl', help='Disable listener SSL', rich_help_panel='Listener Configs'),
    comms_port:     int         = typer.Option(None, '--comms-port', help='If set, will generate a payload profile for the listener same configs but this port', rich_help_panel='Listener Configs'),
    bind_port:      int         = typer.Option(443, '--bind-port', help='Port the listener will bind to', rich_help_panel='Listener Configs'),
    bind_host:      str         = typer.Option(..., '--bind-host', help='Host the listener will bind to', rich_help_panel='Listener Configs'),
    hosts:          List[str]   = typer.Option(..., '--host', help='Add a rotational host for C2 communications (flag can be used multiple times)', rich_help_panel='Listener Configs'),
    response_type:  DataFormat  = typer.Option(..., '--resp-fmt', help='Data format to use for server HTTP response', rich_help_panel='Listener Configs', case_sensitive=False),
    request_type:   DataFormat  = typer.Option(..., '--req-fmt', help='Data format to use for client HTTP request', rich_help_panel='Listener Configs', case_sensitive=False),
    obfsleep:       ObfSleep    = typer.Option(..., '--obfsleep', help='Sleep obfuscation method', rich_help_panel='Listener Configs', case_sensitive=False),
    flavor:         str         = typer.Option(..., '--flavor', help='C2 communication flavor. Used in OpenAI queries for URIs, headers, HTTP requests', rich_help_panel='Listener Configs'),
    user_agent:     UserAgent   = typer.Option(..., '--user-agent', help='User agent to use for the listener', rich_help_panel='Listener Configs', case_sensitive=False),
    auth_count:     int         = typer.Option(1, '--auth-count', help='Number of authentication keys', rich_help_panel='Listener Configs'),
    ota:            bool        = typer.Option(False, '--ota', help='Enable one-time authentication', rich_help_panel='Listener Configs'),
    die:            bool        = typer.Option(False, '--die', help='Kill the payload if internet is unavailable on lanuch', rich_help_panel='Listener Configs'),
    proxy:          str         = typer.Option(None, '--proxy', help='Proxy URL for payload connections', rich_help_panel='Listener Configs'),
    
    # operator configurations
    admins:         List[str]   = typer.Option(['admin'], '--admin', help='Add a commander admins (flag can be used multiple times)', rich_help_panel='Operator Configs'),
    operators:      List[str]   = typer.Option(None, '--operator', help='Add a commander operators (flag can be used multiple times)', rich_help_panel='Operator Configs'),
    
    # miscellaneous configurations
    no_autosave:    bool        = typer.Option(False, '--no-autosave', help='Disable profile autosave', rich_help_panel='Miscellaneous Configs'),
    cmd_host:       str         = typer.Option('0.0.0.0', '--cmd-host', help='Host the commander will bind to', rich_help_panel='Miscellaneous Configs'),
    cmd_port:       int         = typer.Option(8443, '--cmd-port', help='Port the commander will bind to', rich_help_panel='Miscellaneous Configs'),
    
    # badger-builder options
    outfile:        Path        = typer.Option('profile.json', '--outfile', file_okay=True, writable=True, help='Output file for the profile', rich_help_panel='Badger Builder Options'),
    temperature:    float       = typer.Option(1.2, '--temp', help='Temperature for OpenAI GPT-3 queries. Between 0.0 and 2.0. Higher values cause more randomness, while lower are more focused', rich_help_panel='Badger Builder Options'),
    debug:          bool        = typer.Option(False, '--debug', help='Enable debug logging', rich_help_panel='Badger Builder Options')
):      
    init_logger(debug)
    load_dotenv()

    logger.info('Badger is building your profile...')

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
    listener['port'] = bind_port
    listener['sleep'] = sleep
    listener['jitter'] = jitter
    listener['ssl'] = not disable_ssl
    listener['auth_count'] = auth_count
    listener['auth_type'] = ota
    listener['die_offline'] = die
    listener['useragent'] = get_ua_string(user_agent)
    listener['obfsleep'] = obfsleep.value
    listener['rotational_host'] = ','.join(hosts)

    if proxy:
        listener['proxy'] = proxy

    # get ChatGPT's input for dynamic configs
    logger.info(f'Querying OpenAI for "{flavor}" flavored listener configs...')
    badger_ai = BadgerBuilderAI(flavor, temperature)
    
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
        if 'BadgerPlaceholder' in body and body.count('BadgerPlaceholder') == 1:
            break
        else:
            logger.error('OpenAI returned malformed HTTP request body... retrying')

    request = body.split('BadgerPlaceholder', 1)
    listener['prepend'] = request[0]
    listener['append'] = request[1]
    

    # get server-side response body
    while True:
        body = badger_ai.http_body_query(response_type.value, client_side=False)
        if 'BadgerPlaceholder' in body and body.count('BadgerPlaceholder') == 1:
            break
        else:
            logger.error('OpenAI returned malformed HTTP response body... retrying')

    response = body.split('BadgerPlaceholder', 1)
    listener['prepend_response'] = response[0]
    listener['append_response'] = response[1]


    # get empty server response
    listener['empty_response'] = badger_ai.empty_resp_query(response_type.value)

    # setup payload profile, if necessary
    if comms_port and comms_port != bind_port:
        logger.info('Comms port is defined and is different from bind port - creating corresponding payload profile... ')
        profile['payload_config'] = {}

        # copy listener configs to payload profile
        profile['payload_config']['http-custom'] = listener

        # change port to comms port
        profile['payload_config']['http-custom']['port'] = comms_port


    # dump to file!
    with open (outfile, 'w') as f:
       f.write(json.dumps(profile, indent=4))
    
    logger.info(f'Profile saved to {outfile}')


if __name__ == '__main__':
    app(prog_name='c4-profiler')
