import openai
import os

from badger_builder.logger import logger

AI_DO_NOT_USE_LANG = 'Do not use obvious test/sample values, strings and patterns. For example, do not include strings like "example", "test", "sample", "placeholder", "abc" or "123".'


class BadgerBuilderAI:

    def __init__(self, flavor, temperature):
        self.flavor = flavor
        self.temperature = temperature
    

    def openai_query(self, query, max_tokens=500):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        try:
            response = openai.Completion.create(
                model='text-davinci-003',
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
        logger.debug('Querying OpenAI for URIs')
        query = f'Generate between 4 and 8 HTTP URIs separated by a newline. URIs should being with a slash. Do not include full URLs. All URIs should be at least 2 directories deep. The URI list should contain both files (ending with a common web file extension) and directories. Use only URL safe characters. The URI theme is {self.flavor}. {AI_DO_NOT_USE_LANG}'
        
        raw_uris = self.openai_query(query)
        return [uri[1:] for uri in raw_uris.splitlines()]


    def http_header_query(self, send_fmt, recv_fmt, client_side=True):
        side = 'server-side'
        if client_side:
            side = 'client-side'
        
        logger.debug(f'Querying OpenAI for {side} HTTP headers')

        query = f'generate 3-10 HTTP headers for a {side} application that accepts {recv_fmt} and is sending {send_fmt}. Return the headers in valid JSON format (non-final headers should end with a comma). The headers belong to an {self.flavor} themed application. {AI_DO_NOT_USE_LANG} (example: the value of a cookie header should be a legitmate cookie)'
        headers = self.openai_query(query)
        
        # the model seems to like returning JSON prepened by a period and newlne
        return headers[headers.find("{"):]


    def http_body_query(self, fmt, client_side=True):
        side = 'server-side'
        if client_side:
            side = 'client-side'

        logger.debug(f'Querying OpenAI for {side} HTTP body')
        
        query = f'generate a {side} HTTP body in valid {fmt} format. In a string value of the body, that is most likely to contain a large blob of data, set a single string value to "DataBlobPlaceholder" (camel-cased and no spaces in this string) (there is an equal chance this value is placed anywhere in the body). The body should be between 10 and 40 lines. The HTTP body belongs to an {self.flavor} themed application. {AI_DO_NOT_USE_LANG} (example: the value of a session parameter should be a legitmate session token).'
        return self.openai_query(query)
    

    def empty_resp_query(self, fmt):
        logger.debug('Querying OpenAI for empty HTTP response')
        
        query = f'generate a HTTP response body in valid {fmt} format that contains a server response to an invalid client request, or client request to a non-existent URI. Provide only the HTTP body, do not provide HTTP headers or any other HTTP response content. The HTTP response belongs to an {self.flavor} themed application. {AI_DO_NOT_USE_LANG}'
        return self.openai_query(query)



