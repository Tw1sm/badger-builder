<h1 align="center">
<br>
<img height=250 src=.assets/badger-transparent.png >
<br>
badger-builder
</h1>

`badger-builder` is an AI-assisted tool for generating dynamic Brute Ratel C4 profiles. Simply provide `badger-builder` a *flavor* for your desired profile and it will prompt OpenAI for fitting configurations.

Listener/payload profile configs that are AI generated:
- C2 URIs
- Request/response HTTP headers
- HTTP body data prepended and appended to C2 requests/responses
- The server's *empty-response* HTTP body

HTTP body data can be generated in 3 formats (response and request format do not need to be the same):
- JSON
- XML
- JavaScript

Tested on Brute Ratel 1.4.4

Currently only HTTP listener profile configs are supported (no DoH support)

## Install
`badger-builder` can be installed by cloning this repository and running `pip3 install .` and subsequently executed from PATH with `badger-builder`

## Usage

## Examples

## Development
`badger-builder` uses Poetry to manage dependencies. Install from source and setup for development with:
```
git clone https://github.com/tw1sm/badger-builder
cd badger-builder
poetry install
poetry run badger-builder --help
```

## Improvements
- [ ] Better OpenAI prompts
- [ ] DoH listener integration
- [ ] More prepend/append data formats
- [ ] `autorun` actions such as setting kill date, chid, malloc/threadex settings