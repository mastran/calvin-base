# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ericsson AB
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

import operator
from calvin.utilities.calvinlogger import get_logger


_log = get_logger(__name__)


class Compare(object):

    def relation(self, rel):
        try:
            return {
                        '<': operator.lt,
                        '<=': operator.le,
                        '=': operator.eq,
                        '!=': operator.ne,
                        '>=': operator.ge,
                        '>': operator.gt,
                    }[rel]
        except KeyError:
            _log.warning('Invalid operator %s, will always produce FALSE as result' % str(self.relation))
            return lambda x,y: False

def register(node=None, actor=None):
    return Compare()