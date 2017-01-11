# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ericsson AB
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

import os
from datetime import datetime, timedelta
try:
    import jwt
    HAS_JWT = True
except:
    HAS_JWT = False
from calvin.utilities.security import decode_jwt, encode_jwt
from calvin.utilities.calvin_callback import CalvinCB
from calvin.runtime.north.authorization.policy_decision_point import PolicyDecisionPoint
from calvin.runtime.north.authorization.policy_retrieval_point import FilePolicyRetrievalPoint
from calvin.utilities.calvinlogger import get_logger
from calvin.utilities import calvinconfig

_log = get_logger(__name__)
_conf = calvinconfig.get()
_sec_conf = _conf.get("security","security_conf")

registration_attempt=0

class Authorization(object):
    """Authorization helper functions"""

    def __init__(self, node):
        self.authz_server_id = None
        self.node = node
        try:
            if 'authorization' in _sec_conf and 'procedure' in _sec_conf['authorization']:
                if _sec_conf['authorization']['procedure'] == "local":
                    self.pdp = PolicyDecisionPoint(self.node, _sec_conf['authorization'] if _sec_conf else None)
                    try:
                        self.prp = FilePolicyRetrievalPoint(_sec_conf['authorization']["policy_storage_path"])
                    except:
                        self.prp = FilePolicyRetrievalPoint(os.path.join(os.path.expanduser("~"), 
                                                                         ".calvin", "security", "policies"))
                    self.authz_server_id = self.node.id
                elif 'server_uuid' in _sec_conf['authorization']:
                    self.authz_server_id = _sec_conf['authorization']['server_uuid']
            else:
                self.authz_server_id = None
        except Exception:
            self.authz_server_id = None

    def decode_request(self, data, callback):
        """Decode the JSON Web Token in the data."""
        _log.debug("decode_request:\n\tdata={}\n\tcallback={}".format(data, callback))
        decode_jwt(data["jwt"], data["cert_name"], self.node,
                  callback=CalvinCB(self._decode_request_cb,
                      callback=callback))

    def _decode_request_cb(self, decoded, callback):
        _log.debug("_decode_request_cb\n\tDecoded={}\n\tCallback={}".format(decoded, callback))
        callback(decoded=decoded)

    def encode_response(self, request, response, audience=None):
        """Encode the response to the request as a JSON Web Token."""
        jwt_payload = {
            "iss": self.node.id, 
            "aud": request["iss"] if audience is None else audience, 
            "iat": datetime.utcnow(), 
            "exp": datetime.utcnow() + timedelta(seconds=60),
            "response": response
        }
        if "sub" in request:
            jwt_payload["sub"] = request["sub"]
        # Create a JSON Web Token signed using the authorization server's private key.
        return encode_jwt(jwt_payload, self.node)

    def register_node(self):
        """Register node attributes for authorization."""
        _log.debug("register_node")
        if _sec_conf and "authorization" in _sec_conf:
            # TODO: the node should contact the authz server regularly (once a day?), 
            #       otherwise it should be removed from the registered_nodes list on the authz server.
            try:
                if _sec_conf['authorization']['procedure'] == "external":
                    if not HAS_JWT:
                        _log.error("Security: Install JWT to use external server as authorization method.")
                        return
                    if self.authz_server_id:
                        #Authorization server id configured in calvin config file, let's use it
                        _log.debug("Authorization server id configured in calvin config file, let's use it. authz_server_id={}".format(self.authz_server_id))
                        self.register_node_external()
                    else:
                        #No authorization servered configured, let's try to find one in storage
                        _log.debug("No authorization server configured, let's try to find one in storage")
                        self.node.storage.get_index(['external_authorization_server'],
                                                    CalvinCB(self._register_node_cb))
                else:
                    self.pdp.register_node(self.node.id, self.node.attributes.get_indexed_public_with_keys())
            except Exception as e:
                _log.error("Node could not be registered for authorization - %s" % str(e))

    def _register_node_cb(self, key, value):
        import random
        import time
        global registration_attempt
        _log.debug("_register_node_cb:\n\tkey={}\n\tvalue={}\n\tattempt={}".format(key,value, registration_attempt))
        if value:
            nbr = len(value)
            #For loadbalanding of authorization server, randomly select
            # one of the found authorization servers
            rand = random.randint(0, nbr-1)
            self.authz_server_id = value[rand]
            self.register_node_external()
        elif registration_attempt<10:
            time_to_sleep = 1+registration_attempt*registration_attempt*registration_attempt
            _log.error("No authorization server found, try again after sleeping {} seconds".format(time_to_sleep))
            #Wait for a while and try again
            time.sleep(time_to_sleep)
            registration_attempt = registration_attempt+1
            self.node.storage.get_index(['external_authorization_server'],
                                        CalvinCB(self._register_node_cb))
        else:
            raise Exception("No athorization server accepting external clients can be found")

    def register_node_external(self):
        """Register node attributes for external authorization"""
        # FIXME: should this include certificate exchange?
        payload = {
            "iss": self.node.id, 
            "aud": self.node.authorization.authz_server_id, 
            "iat": datetime.utcnow(), 
            "exp": datetime.utcnow() + timedelta(seconds=60),
            "attributes": self.node.attributes.get_indexed_public_with_keys()
        }
        # Create a JSON Web Token signed using the node's Elliptic Curve private key.
        jwt_request = encode_jwt(payload, self.node)
        # Send registration request to authorization server.
        self.node.proto.authorization_register(self.node.authorization.authz_server_id, 
                                          CalvinCB(self._register_node_external_cb), 
                                          jwt_request)

    def _register_node_external_cb(self, status):
        if not status or status.status != 200:
            _log.error("Node could not be registered for authorization")
        else:
            _log.debug("Successfully registered with authorization server")
