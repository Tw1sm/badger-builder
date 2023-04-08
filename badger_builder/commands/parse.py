from pathlib import Path
import typer
import json
import copy

from badger_builder.logger import logger, init_logger
from badger_builder.lib import utils

app = typer.Typer()
COMMAND_NAME = 'parse'
HELP = 'Print a sample BRc4 HTTP request and response using profile configs'


@app.callback(no_args_is_help=True, invoke_without_command=True)
def main(
    profile: Path = typer.Argument(..., help='Path to the JSON profile to parse', exists=True, file_okay=True, dir_okay=False, readable=True),
):      
    init_logger(False)
    logger.info('Printing sample HTTP traffic...')
    
    with open(profile, 'r') as f:
        profile = json.load(f)
    
    utils.print_traffic_profile(profile)
