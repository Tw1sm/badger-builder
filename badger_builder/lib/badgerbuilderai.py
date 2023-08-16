import openai
import os

from badger_builder.logger import logger

AI_DO_NOT_USE_LANG = 'Avoid obvious test/sample values or patterns (e.g., "example", "test", "sample", ' \
                     '"placeholder", "abc", "123").'


class BadgerBuilderAI:

    def __init__(self, flavor, temperature, model):
        self.flavor = flavor
        self.temperature = temperature
        self.model = model
    

    def openai_query(self, query, max_tokens=500):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        try:
            response = openai.Completion.create(
                model=self.model,
                prompt=query,
                temperature=self.temperature,
                stream=False,
                max_tokens=max_tokens,
                n=1
            )
            return response.choices[0]['text'].strip()
        except Exception as e:
            logger.error(f'Error querying OpenAI - {e}')
            exit(1)


    def uri_query(self):
        logger.info('Querying OpenAI for URIs')
        query =  'Create 4-8 HTTP URIs, each starting with a slash and having at least 2 directories deep. ' \
                 'Ensure the URIs contain both files (with common web file extensions) and directories, and ' \
                 f'use only URL-safe characters. The theme is {self.flavor}. {AI_DO_NOT_USE_LANG}' \
                 'Return only URIs (no list formatting) separated by a newline.'

        raw_uris = self.openai_query(query)
        return [uri[1:] if uri.startswith('/') else uri for uri in raw_uris.splitlines()]


    def http_header_query(self, send_fmt, recv_fmt, client_side=True):
        side = 'server-side'
        if client_side:
            side = 'client-side'
        
        logger.info(f'Querying OpenAI for {side} HTTP headers')

        query = f'Generate 3-10 HTTP headers for a {side} application accepting {recv_fmt} and sending {send_fmt}. ' \
                 'Present the headers in valid JSON format, with non-final headers ending in a comma. Headers should ' \
                 f'relate to a {self.flavor} themed application. {AI_DO_NOT_USE_LANG} Ensure legitimate values (e.g., valid cookie for a cookie header).'
        
        headers = self.openai_query(query)
        
        # the model seems to like returning JSON prepened by a period and newlne
        return headers[headers.find("{"):]


    def http_body_query(self, fmt, client_side=True):
        side = 'server-side'
        if client_side:
            side = 'client-side'

        logger.info(f'Querying OpenAI for {side} HTTP body')
        
        query = f'Create a {side} HTTP body in valid {fmt} format, containing 10-40 lines, for an {self.flavor} themed '\
                 'application. Replace a string value likely to hold a large data blob with "DataBlobPlaceholder" ' \
                 f'(camel-cased, no spaces). Place this value randomly within the body. {AI_DO_NOT_USE_LANG} ' \
                 'Use legitimate values (e.g., valid session token for a session parameter).'
        
        return self.openai_query(query)
    

    def empty_resp_query(self, fmt):
        logger.info('Querying OpenAI for empty HTTP response')
        
        query = f'Create an HTTP response body in valid {fmt} format for an {self.flavor} themed application, representing ' \
                 'a server response to an invalid client request or a client request to a non-existent URI. ' \
                 f'Exclude HTTP headers and other response content. {AI_DO_NOT_USE_LANG}'
        
        return self.openai_query(query)



