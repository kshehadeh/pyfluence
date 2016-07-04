# PyFluence
----
A Python 2.7 REST API client for Atlassian Confluence

<!--[![Build Status](https://travis-ci.org/PyGithub/PyGithub.svg?branch=master)](https://travis-ci.org/PyGithub/PyGithub)-->
<!--[![PyPi](https://img.shields.io/pypi/dm/pygithub.svg)](https://pypi.python.org/pypi?%3Aaction=search&term=pygithub&submit=search)-->
<!--[![readthedocs](https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat)](http://pygithub.readthedocs.org/en/stable)-->
<!--[![License](https://img.shields.io/badge/license-LGPL-blue.svg)](https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License)-->

This library lets you view, edit, delete entities in an instance of Atlassian Confluence using its REST API

[Confluence API v3]: https://docs.atlassian.com/confluence/REST/latest/
[Confluence]: https://www.atlassian.com/software/confluence

## Simple Demo

```python
from pyfluence import Confluence

# First create a Confluence instance:
confluence = Confluence("admin","admin","http://localhost:1990/confluence")

# Then create a space
space_ob = confluence.create_space("TEST","Test Space","Test Space Description")

# Then create a page in that space
content_ob = confluence.create_content(
    space_key=space_ob['key'],
    type="page",
    title="Test Parent Page",
    html_markup="<h1>This is a test page</h1>",
)

# Then you can update the page
self.confluence.update_content(
    space_key=space_ob['key'],
    id=content_ob['id'],
    html_markup="<h1>This is an update</h1>",
    update_type=co.UPDATE_REPLACE
)
```
