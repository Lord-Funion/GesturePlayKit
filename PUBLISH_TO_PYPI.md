# Publish GesturePlayKit 1.3.0 to PyPI

Pushing the files to GitHub **does not publish a package to PyPI**. The repository contains source that can be installed with `python -m pip install .` locally. Before a PyPI release, ensure the distribution name is available and you control the account authorized to publish it.

## Check the release

```powershell
py -m pip install --upgrade build twine
py -m pytest -q
py -m build
py -m twine check dist/*
```

## Upload securely

```powershell
py -m twine upload dist/*
```

Use username `__token__` and the secret PyPI token as password, or use trusted publishing if configured. **Never** post the token in GitHub, screenshots, conversations or issue reports. PyPI rejects duplicate version uploads; increment the version for any subsequent release.

As of this source release, there is no claim that version 1.3.0 has been uploaded to PyPI.
