import os

import requests
import time

METHOD_POST = "post"
METHOD_GET = "get"
METHOD_DELETE = "delete"
METHOD_PUT = "put"
METHOD_OPTIONS = "options"
METHOD_HEAD = "head"

UPDATE_PREPEND = "prepend"
UPDATE_APPEND = "append"
UPDATE_REPLACE = "replace"


class ConfluenceResponseError(Exception):
    """
    Raised when a non-200 response is received
    """

    def __init__(self, status_code, msg):
        self.status_code = status_code
        super(ConfluenceResponseError, self).__init__(msg)


class ConfluenceContentNotFoundError(Exception):
    """
    Raised when content could not be found (ConfluenceResponseError(404))
    """

    def __init__(self, content_id, msg):
        self.content_id = content_id
        super(ConfluenceContentNotFoundError, self).__init__(msg)


class ConfluenceIncompatibleRepresentationError(Exception):
    """
    Raised when an action is attempted that is not possible because the representation of content is not
    compatible (e.g. combining "storage" content with "wiki" content)
    """

    def __init__(self, content_id, representation_expected, representation_given, message=""):
        self.content_id = content_id
        self.representation_expected = representation_expected
        self.representation_given = representation_given

        super(ConfluenceIncompatibleRepresentationError, self).__init__(message)


class ConfluenceInvalidInputError(Exception):
    """
    This is raised when the user is trying to perform an action but the given input is not sufficient to
    execute the action.
    """
    pass


class Confluence(object):
    """
    A simple Atlassian Confluence REST API client.  Initialize the object with the username, password and host url
        (excluding the path to the API (e.g. http://myconfluence.company.com/wiki).  Then you can use the associated
        methods to retrieve data from your instance of confluence.

    """

    def __init__(self, username, password, host):
        """
        Initialize with username, password and host info
        :param username: The username to login to confluence with
        :param password: The password to login to confluence with
        :param host: The host url (excluding the path to the API (e.g. http://myconfluence.company.com/wiki)
        """
        self.username = username
        self.password = password
        self.host = host

    def _query(self, path, data=None, method=METHOD_GET, expand=(), files=None, headers=None, sync=True):
        """
        Generalized Confluence REST API method.  All requests come through this method eventually.
        :param path: The path to the API (excluding the root)
        :param data: The input to the API
        :param method: The method to use to access the data. If the method is GET then the data value will be
            interpreted as query parameters.  Otherwise it will be converted to JSON and placed in the body of the
            request.
        :param sync: If true and this api call executes a long running task then it won't return until the
                task is complete.
        :return: Returns the JSON representation of the result from the API.
        """

        def generate_full_url(path, host, api="rest/api/"):
            path = path[1:] if path[0] == "/" else path
            host = host[0:-1] if host[-1] == "/" else host
            return "{host}/{api}{path}".format(host=host, api=api, path=path)

        # string leading slash
        url = generate_full_url(path,self.host)

        data = data or {}
        data['expand'] = ",".join(expand)

        # use form encoding for params if a file is given, otherwise assume that we can
        #   put JSON in the body.
        json_params = form_params = None
        if files:
            form_params = data
        else:
            json_params = data

        if method == METHOD_POST:
            response = requests.post(url, data=form_params, json=json_params, auth=(self.username, self.password),
                                     files=files, headers=headers)
        elif method == METHOD_PUT:
            response = requests.put(url, data=form_params, json=json_params, auth=(self.username, self.password),
                                    files=files, headers=headers)
        elif method == METHOD_DELETE:
            response = requests.delete(url, auth=(self.username, self.password), files=files, headers=headers)
        elif method == METHOD_OPTIONS:
            response = requests.options(url, auth=(self.username, self.password))
        elif method == METHOD_HEAD:
            response = requests.head(url, auth=(self.username, self.password))
        else:
            response = requests.get(url, params=data, auth=(self.username, self.password), headers=headers)

        if response.status_code >= 400:
            raise ConfluenceResponseError(response.status_code, response.text)

        if response.status_code == 204:
            # no content to return
            return None

        if response.status_code == 202 and sync == True:
            # poll until complete
            while response.status_code == 202:
                status_url = generate_full_url(path=response.json()['links']['status'], host=self.host,api="")
                response = requests.get(status_url, auth=(self.username, self.password))
                time.sleep(1)

        return response.json()

    def _paginated_query(self, path, data=None, limit=25, start=0, expand=(), child_node=None):
        """
        For queries that return paginated data, this will retrieve all pages of the result, not just the first.
        :param path: (see _query)
        :param data:  (see _query)
        :param limit: The number of items to retrieve at once.
        :param start: Which item # to start at.
        :param child_node: If the returned list is not in the root of the resulting object, then specify the
            child node in which to find the "results" field and the size or totalSize field.
        :return: Returns a dict containing the total number of items found and the results themselves.
        """
        data = data or {}

        # first at least one iteration (there's no do while in python)
        remaining = 1
        results = []
        result_ob = None
        total_size = 0
        while remaining > 0:

            data['limit'] = limit
            data['start'] = start

            # Get page and append to final list
            result_ob = self._query(path=path, data=data, method=METHOD_GET, expand=expand)
            result_ob_root = result_ob if not child_node else result_ob[child_node]
            results.extend(result_ob_root['results'])

            # need to have a ceiling in case the query is too general
            if len(results) >= 1000:
                break

            # Calculate the remaining items after we have gotten the last batch and increment the new start
            total_size = result_ob_root['totalSize'] if 'totalSize' in result_ob_root else result_ob_root['size']
            remaining = total_size - (result_ob_root['start'] + result_ob_root['size'])
            start += limit

        if result_ob:
            # sanity check
            assert (len(results) == total_size)

        return {
            "size": len(results),
            "results": results
        }

    def get_content(self, id, expand=("space", "body.view", "version", "container")):
        """
        Gets the content with the given ID
        :param id: The ID of the content
        :param expand: The specific parts of the content entity to return in the result.
        :return: The JSON representation of the content.
        """
        expand = expand or ()
        try:
            result = self._query('/content/' + str(id),
                                 expand=expand,
                                 method=METHOD_GET)
            return result
        except ConfluenceResponseError, e:
            if e.status_code == 404:
                return None
            else:
                raise e

    def search(self, cql, expand=None):
        """
        Executes a CQL query to retrieve information about the content.
        :param cql: The CQL query
            (see https://developer.atlassian.com/confdev/confluence-server-rest-api/advanced-searching-using-cql)
        :param expand: The parts of each page to return in the results (avoid using body.view)
        :return: Returns a dict containing the list of objects found and the total number found
        """
        expand = expand or []
        return self._paginated_query('/search', data={"cql": cql, "expand": ",".join(expand)})

    def create_space(self,key,name,description=""):
        """
        Creates a new space
        :param key: The unique key name (must be 10 characters or less)
        :param name: The friendly name of the space
        :param description: An optional description in plain text.
        :return: Returns the created space along with its ID
        """
        if not key:
            raise ConfluenceInvalidInputError("You must provide a unique space key to add a space")

        if not name:
            raise ConfluenceInvalidInputError("You must provide a valid name to add a space")

        param_dict = {
            "name": name,
            "key": key,
            "description":
                {
                    "plain": {
                        "value": description if not None else "",
                        "representation": "plain"
                    }
                }
        }

        return self._query("space/", data=param_dict, method=METHOD_POST)

    def create_content(self, space_key=None, type="page", title=None,
                       html_markup=None, wiki_markup=None, parent_content_id=None):
        """
        :param type: The page type which can be "page", "blogpost", etc. (required)
        :param title: Then title of the page (required)
        :param space_key: The key for the confluence space to add the content to (required)
        :param parent_content_id: The ID of the content that should be the parent (if None, will be in the root of the space)
        :param html_markup: If you want to add markup in the form of HTML, use this param
        :param wiki_markup: If you want to add markup in wiki format, use this param
        :return: Returns the object that was added as given by the confluence API
        """
        if not space_key:
            raise ConfluenceInvalidInputError("You must provide a valid space key to add content")

        if not title:
            raise ConfluenceInvalidInputError("You must provide a valid content type to add content")

        if not type:
            type = "page"

        param_dict = {
            "title": title,
            "space": {
                "key": space_key
            },
            "body":
                {
                    "storage": {
                        "value": html_markup or wiki_markup,
                        "representation": "storage" if html_markup else "wiki"
                    }
                },
            "type": type
        }

        if parent_content_id:
            param_dict['ancestors'] = [{"id": parent_content_id}]

        return self._query("content/", data=param_dict, method=METHOD_POST)

    def delete_content(self, id):
        """
        Deletes content
        :param id: The ID of the content to delete
        :return: Nothing returned if successful.  ConfluenceResponseError raised if failure.
        """
        self._query("content/%s"%str(id), method=METHOD_DELETE)

    def delete_space(self, key):
        """
        Deletes a space
        :param key: The key of the space to delete
        :return: Nothing returned if successful.  ConfluenceResponseError raised if failure.
        """
        self._query("space/%s"%str(key), method=METHOD_DELETE)

    def update_content(self, id, html_markup=None, wiki_markup=None, update_type=UPDATE_REPLACE):
        """
        Update a page either by replacing the entire page or prepending or appending content
        :param id:  The id of the page to update
        :param html_markup: The HTML markup to update with ('storage' representation)
        :param wiki_markup: The Wiki markup to update with ('wiki' representation)
        :param update_type: Whether to replace, prepend or append (UPDATE_REPLACE, UPDATE_PREPEND, UPDATE_APPEND)
        :return:
        """
        # first get information about the page
        page = self.get_content(id, expand=("space", "body.view", "version", "container", "ancestors"))
        if not page:
            raise ConfluenceContentNotFoundError(id, "Unable to find updateable page during page update request")

        representation = page['body']['view']['representation']
        body = page['body']['view']['value']

        if representation == 'storage' and not html_markup and update_type != UPDATE_REPLACE:
            raise ConfluenceIncompatibleRepresentationError(content_id=id, representation_expected=representation,
                                                            representation_given="wiki")

        if representation == 'wiki' and not wiki_markup and update_type != UPDATE_REPLACE:
            raise ConfluenceIncompatibleRepresentationError(content_id=id, representation_expected=representation,
                                                            representation_given="storage")

        new_value = html_markup or wiki_markup
        final_value = ""
        if update_type == UPDATE_REPLACE:
            final_value = new_value
        elif update_type == UPDATE_APPEND:
            final_value = body + new_value
        elif update_type == UPDATE_PREPEND:
            final_value = new_value + body

        param_dict = {
            "id": str(id),
            "title": page['title'],
            "space": {
                "key": page['space']['key']
            },
            "body":
                {
                    "storage": {
                        "value": final_value,
                        "representation": "storage" if html_markup else "wiki"
                    }
                },
            "version": {
                "number": page['version']['number'] + 1
            },
            "type": page['type']
        }

        if 'ancestors' in page and page['ancestors']:
            anc = page['ancestors'][-1]
            del anc['_links']
            del anc['_expandable']
            del anc['extensions']
            param_dict['ancestors'] = [anc]

        return self._query("content/%s" % str(id), data=param_dict, method=METHOD_PUT)

    def get_content_info(self, id):
        """
        Retrieves information about the given page
        :param auth: The username and password tuple
        :param page_id: The ID of the page to get info about
        :return: The response as JSON
        """
        return self.get_content(id, expand=None)

    def get_content_ancestors(self, id):
        """
        Get basic content information plus the ancestors property
        :param id: The ID of the page to get info about
        :return: Returns ancestor information for the given page.
        """
        content = self.get_content(id, expand=("ancestors"))
        return content.json()['ancestors']

    def add_content_attachment(self, file, id):
        """
        Adds an attachment to the given page but will add a new version if a file with the given name
        already exists.
        :param file: The file to add
        :param id: The ID of the content to add to
        :return: The result of the query.
        """
        # first, determine if there's an attachment with this name
        add_new_version = None
        filename = os.path.basename(file)
        attachments = self.get_attachments(id)
        for a in attachments['results']:
            if a['title'] == filename:
                add_new_version = a

        if not add_new_version:
            r = self._query("content/{id}/child/attachment".format(id=id),
                            method=METHOD_POST,
                            files={'file': open(file, 'rb')},
                            data={'comment': 'new version of %s' % file, 'minorEdit': True},
                            headers=({'X-Atlassian-Token': 'no-check'}))

        else:
            url = "content/{id}/child/attachment/{attachment_id}/data".format(id=id,
                                                                              attachment_id=add_new_version['id'])
            r = self._query(url,
                            method=METHOD_POST,
                            files={'file': open(file, 'rb')},
                            data={'minorEdit': True, 'comment': 'new version of %s' % file},
                            headers=({'X-Atlassian-Token': 'no-check'}))

        return r

    def get_attachment(self, attachment_id):
        """
        Get the attachment with the given id (attachment IDs start with "att")
        :param auth:
        :param page_id:
        :param attachment_id: The ID of the attachment content (
        :return:
        """
        return self.get_content(attachment_id, expand=("ancestors", "version", "space", "container"))

    def get_attachments(self, id):
        """
        Gets a list of all the attachments that are children of the given content
        :param id:
        :return: An object containing attachment data for the given parent content
        """
        return self._paginated_query(path="content/{id}/child".format(id=id), expand=("attachment",),
                                     child_node="attachment")
