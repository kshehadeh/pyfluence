import sys
import argparse

from cement.core.controller import CementBaseController, expose


class PyfluenceBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = "my application does amazing things"
        arguments = [
            (['--server'], dict(help="The confluence server")),
            (['--username'], dict(help="Username to login with")),
            (['--password'], dict(help="Password to login with")),
        ]

    @expose(help="base controller default command", hide=True)
    def default(self):
        print("Inside MyAppBaseController.default()")

    @expose(help="another base controller command")
    def command1(self):
        print("Inside MyAppBaseController.command1()")

