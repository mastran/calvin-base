# -*- coding: utf-8 -*-

# Copyright (c) 2015 Ericsson AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from calvin.actor.actor import Actor, manage, condition, stateguard
from calvin.utilities.calvinlogger import get_logger

_log = get_logger(__name__)


class HTTPPut(Actor):
    """
    PUT data to URL, retrieving reply

    Input:
      URL : URL to get
      params : Optional parameters to request as a JSON dictionary
      header: JSON dictionary with headers to include in request
      data : data to send to URL
    Output:
      status: 200/404/whatever
      header: JSON dictionary of incoming headers
      data : body of request
    """

    @manage()
    def init(self):
        self.setup()

    def did_migrate(self):
        self.setup()

    def setup(self):
        self.request = None
        self.reset_request()
        self.use('calvinsys.network.httpclienthandler', shorthand='http')
        self.use('calvinsys.native.python-json', shorthand='json')

    def reset_request(self):
        if self.request:
            self['http'].finalize(self.request)
            self.request = None
        self.received_headers = False

    @stateguard(lambda self: self.request is None)
    @condition(action_input=['URL', 'params', 'header', 'data'])
    def new_request(self, url, params, header, data):
        url = url.encode('ascii', 'ignore')
        self.request = self['http'].put(url, params, header, data)
        return ()

    @stateguard(lambda self: self.request and not self.received_headers and self['http'].received_headers(self.request))
    @condition(action_output=['status', 'header'])
    def handle_headers(self):
        self.received_headers = True
        status = self['http'].status(self.request)
        headers = self['http'].headers(self.request)
        return (status, headers)

    @stateguard(lambda self: self.received_headers and self['http'].received_body(self.request))
    @condition(action_output=['data'])
    def handle_body(self):
        body = self['http'].body(self.request)
        self.reset_request()
        return (body,)

    @stateguard(lambda self: self.received_headers and self['http'].received_empty_body(self.request))
    @condition()
    def handle_empty_body(self):
        self.reset_request()
        return ()
        
    @stateguard(lambda actor: actor.request and actor['http'].received_error(actor.request))
    @condition()
    def handle_error(self):
        _log.warning("There was an error handling the request")
        self.reset_request()
        return ()

    action_priority = (handle_error, handle_body, handle_empty_body, handle_headers, new_request)
    requires = ['calvinsys.network.httpclienthandler', 'calvinsys.native.python-json']
