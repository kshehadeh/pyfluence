import json

from cement.core.controller import CementBaseController, expose


class SearchController(CementBaseController):
    class Meta:
        label = 'search'
        stacked_on = 'base'
        stacked_type = 'nested'        
        description = "Search for content and return results as JSON"
        arguments = [
            (['--cql'], dict(help="The CQL to use to search", required=True)),
        ]

    @expose(help="Search using a CQL expression ", hide=True)
    def default(self):
        if not self.app.connect_to_confluence():
            self.app.exit_code = 1
            return
        
        results = self.app.confluence.search(self.app.pargs.cql)
        print(json.dumps(results))

