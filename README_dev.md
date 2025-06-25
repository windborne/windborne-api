# Developing this package

To install the local version, run:
```bash
pip install -e .
```

You can then `import windborne` and have it refer to the latest version, or use the `windborne` cli for manual testing.

## Pushing a new version
1. Make sure you've been added to the pypi organization
2. Increment the version in pyproject.toml
3. Run `bash deploy.sh` which will push the pip package

## Unit testing
TODO: create a folder called `test` which uses pytest and imports the package directly.

## Integration testing
These are end-to-end tests, designed primarily to test that the backend gives expected responses when accessed through the cli.
This is a good way to make sure that new cli methods are interacting with the backends in the way that you expect.
They were implemented in ruby thanks to its eloquent testing framework.

To run for the first time:
1. Install ruby dependencies: `gem install rspec`. It expects ruby 3 or greater.
2. Add a file `credentials.json` to the spec folder. This is a git-ignored JSON file containing API keys; ask on zulip for a copy.

Then, run:
```bash
rspec spec
```