# PyFluence
----
A Python 2 and 3 REST API client for Atlassian Confluence

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
    content_type="page",
    title="Test Parent Page",
    html_markup="<h1>This is a test page</h1>",
)

# Then you can update the page
confluence.update_content(
    space_key=space_ob['key'],
    page_id=content_ob['id'],
    html_markup="<h1>This is an update</h1>",
    update_type=co.UPDATE_REPLACE
)
```

## Developing
You can use the Atlassian Developer SDK to run tests.  You can follow the instructions here:  
https://developer.atlassian.com/server/framework/atlassian-sdk/downloads/

On the mac, for example:

    > brew tap atlassian/tap
    > brew install atlassian/atlas-tap/atlassian-plugin-sdk # or upgrade
    > atlas-run-standalone --product confluence
    > python -m unittest pyfluence/tests/test_confluence.py
    
View confluence here:

    http://localhost:1990/confluence
    
   
