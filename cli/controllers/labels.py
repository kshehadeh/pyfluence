from cement.core.controller import CementBaseController, expose

from pyfluence.confluence import ConfluenceResponseError


class LabelController(CementBaseController):
    class Meta:
        label = 'label'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = "Apply or remove labels from content objects"
        arguments = [
            (['--content_id'], dict(help="content ID", required=False)),
            (['--labels'], dict(help="A comma separated list of labels to add/remove", required=True)),
        ]

    def show_controller_header(self, action):
        self.app.show_app_header()
        print("Labeling - {action}".format(**locals()))

    def get_labels(self):
        if self.app.pargs.labels:
            return self.app.pargs.labels.split(",")
        else:
            return []

    def get_content_ids(self):
        content_ids = []
        if not self.app.pargs.content_id:
            ob = self.app.get_stdin_as_object()
            if ob:
                try:
                    for content in ob.results:
                        content_ids.append(content.content.id)
                except KeyError:
                    print("stdin is valid JSON but does not appear to conform to Confluence REST API results.")
                    self.app.close(1)
            else:
                print("You must either specify a content_id parameter or pass search results in stdin")
        else:
            content_ids.append(self.app.pargs.content_id)

        return content_ids

    @expose(help="Add labels to one or more content objects", hide=False)
    def add(self):
        self.app.ensure_connection()
        self.show_controller_header("Add")

        content_ids = self.get_content_ids()
        labels = self.get_labels()
        if content_ids and labels:
            print("Content IDs: {ids}\nLabels: {lb}".format(ids=",".join(content_ids),lb=",".join(labels)))
            print("Working...")
            affected_pages = 0
            for content_id in content_ids:
                try:
                    self.app.confluence.add_labels(content_id, labels)
                    affected_pages += 1
                except ConfluenceResponseError as e:
                    print("Unable to add labels to content with ID {id} - Confluence returned {status}".format(
                        id=content_id, status=e.status_code))
            print("Number of updated pages: {affected_pages}".format(**locals()))
        else:
            print("You must provide a content ID and at least one label")
            self.app.close(1)

    @expose(help="Remove labels from one or more content objects", hide=False)
    def remove(self):
        self.app.ensure_connection()
        self.show_controller_header("Remove")

        content_ids = self.get_content_ids()
        labels = self.get_labels()
        if content_ids and labels:
            print("Content IDs: {ids}\nLabels: {lb}".format(ids=",".join(content_ids),lb=",".join(labels)))
            print("Working...")
            affected_pages = 0
            for content_id in content_ids:
                try:
                    self.app.confluence.remove_labels(content_id, labels)
                    affected_pages += 1
                except ConfluenceResponseError as e:
                    print("Unable to remove labels from content with ID {id} - Confluence returned {status}".format(
                        id=content_id, status=e.status_code))

            print("Number of updated pages: {affected_pages}".format(**locals()))

        else:
            print("You must provide a content ID and at least one label")
            self.app.close(1)
