import json

from cement.core.controller import CementBaseController, expose

from pyfluence.confluence import ConfluenceResponseError


class ContentController(CementBaseController):
    class Meta:
        label = 'content'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = "Add, update and delete content"
        arguments = [
            (['--content_id'], dict(help="A content ID", required=False)),
            (['--space'], dict(help="A confluence space key (e.g. ENG)", required=False)),
            (['--content_location'], dict(help="One of [prepend,append,replace]", required=False, default="after")),
            (['--content_format'], dict(help="One of [html,markdown,wiki]", required=False, default="html")),
            (['--content_title'], dict(help="A content object title", required=False)),
            (['--content_type'], dict(help="Can be one of [page,blogpost,..custom...]", required=False)),
            (['--content_parent_id'],dict(help="The ID of the content object that a new object should "
                                               "be the child of", required=False)),
            (['--content_file'], dict(help="If adding or updating, this is the content to use as content."
                                           "The format of the content can be specified in the content_format argument",
                                      required=False)),

        ]

    def show_controller_header(self, action):
        self.app.show_app_header()
        print("Content - {action}".format(**locals()))

    def get_content(self):
        """
        Helper which gets content either by reading data from the given content_file argument or by looking at
        stdin and returning whatever is in the pipe.
        :return: A string if content was found, otherwise None.
        """
        if not self.app.pargs.content_file:
            return self.app.get_stdin_as_string()

        try:
            with open(self.app.pargs.content_file, 'r') as f:
                content = f.read()
                return content
        except FileNotFoundError:
            print("File {file} could not be found".format(file=self.app.pargs.content_file))
            return None

    @expose(help="Add content to a an existing page or create a new one.", hide=False)
    def add(self):
        self.app.ensure_connection()
        self.show_controller_header("Add")

        content_ids = self.app.get_content_ids()
        content_format = self.app.pargs.content_format
        content = self.get_content()

        if not content_ids:
            # this is meant to create a new page.
            if not self.app.pargs.content_title:
                print("If you are creating a new page then content_title argument is required.")
                self.app.close(1)

            if not self.app.pargs.space:
                print("If you create creating a new page then space argument is required")
                self.app.close(1)

            content_parent_id = self.app.pargs.content_parent_id or None
            content_type = self.app.pargs.content_type or None

            print("Mode: Create")
            print("Title: " + self.app.pargs.content_title)
            print("Type: " + self.app.pargs.content_type)
            print("Space: " + self.app.pargs.space)
            print("Parent ID: " + (self.app.pargs.content_parent_id or "None Given"))

            print("Working...")
            result = self.app.confluence.create_content(space_key=self.app.pargs.space,
                                                        type=content_type,
                                                        title=self.app.pargs.content_title,
                                                        parent_content_id=content_parent_id,
                                                        html_markup=content if content_format == "html" else None,
                                                        wiki_markup=content if content_format == "wiki" else None)
            if result:
                print(json.dumps({
                    "size": 1,
                    "results": [result]
                }))
        else:
            print("Mode: Update")
            print("Content ID(s): " + ",".join(content_ids))

            all_results = {
                "size": 0,
                "results": []
            }
            for cid in content_ids:
                result = self.app.confluence.update_content(content_id=cid,
                                                            update_type = self.app.pargs.content_location,
                                                            html_markup=content if content_format == "html" else None,
                                                            wiki_markup=content if content_format == "wiki" else None)
                if result:
                    all_results["size"] += 1
                    all_results["results"].append(result)

            print (json.dumps(all_results))

    @expose(help="Deletes content objects", hide=False)
    def remove(self):
        self.app.ensure_connection()
        self.show_controller_header("Remove")

        content_ids = self.app.get_content_ids()
        if content_ids:
            print("Content IDs: {ids}".format(ids=",".join(content_ids)))
            print("Working...")
            affected_pages = 0
            failed_to_delete_count = 0
            for cid in content_ids:
                try:
                    self.app.confluence.delete_content(cid)
                    affected_pages += 1
                except ConfluenceResponseError as e:
                    failed_to_delete_count += 1
                    print("Unable to delete content with ID {id} - Confluence returned {status}".format(
                        id=cid, status=e.status_code))

            print("Deleted pages: {affected_pages}\nFailed Delete: {failed_to_delete_count}".format(**locals()))

        else:
            print("You must provide a content ID")
            self.app.close(1)
