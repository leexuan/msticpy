# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Tor Exit Nodes Provider.

Input can be a single IoC observable or a pandas DataFrame containing
multiple observables. Processing may require a an API key and
processing performance may be limited to a specific number of
requests per minute for the account type that you have.

"""
from typing import Tuple, Iterable, Dict, Any

import requests

from .ti_provider_base import TIProvider, LookupResult, TISeverity
from ...nbtools.utility import export
from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


@export
class Tor(TIProvider):
    """Tor Exit Nodes Lookup."""

    _BASE_URL = "https://check.torproject.org/exit-addresses"

    _IOC_QUERIES: dict = {"ipv4": None}

    def __init__(self, **kwargs):
        """Pull down Tor exit node list and save to internal attribute."""
        super().__init__(**kwargs)

        try:
            resp = requests.get(self._BASE_URL)
            tor_raw_list = resp.content.decode()
            self._nodelist = dict(self._tor_splitter(tor_raw_list))
        except ConnectionError:
            self._nodelist = {}

    @staticmethod
    def _tor_splitter(node_list) -> Iterable[Tuple[str, Dict[str, str]]]:
        node_dict: Dict[str, str] = {}
        for line in node_list.split("\n"):
            if not line:
                continue
            fields = line.split(" ", 2)
            if fields[0] == "ExitNode":
                # new record so reset dict
                node_dict = {}
            node_dict[fields[0]] = fields[1] if len(fields) > 1 else None
            if fields[0] == "ExitAddress":
                # yield tuple
                yield fields[1], node_dict

    def lookup_ioc(
        self, ioc: str, ioc_type: str = None, query_type: str = None, **kwargs
    ) -> LookupResult:
        """
        Lookup a single IoC observable.

        Parameters
        ----------
        ioc : str
            IoC Observable value
        ioc_type : str, optional
            IoC Type, by default None (type will be inferred)
        query_type : str, optional
            Specify the data subtype to be queried, by default None.
            If not specified the default record type for the IoC type
            will be returned.

        Returns
        -------
        LookupResult
            The returned results.

        """
        result = LookupResult(
            ioc=ioc,
            ioc_type="ipv4",
            provider="TOR",
            result=bool(self._nodelist),
            reference=self._BASE_URL,
            status=0 if self._nodelist else -1,
        )
        tor_node = self._nodelist.get(ioc)

        if tor_node:
            result.set_severity(TISeverity.warning)
            result.details = {
                "NodeID": tor_node["ExitNode"],
                "LastStatus": tor_node["LastStatus"],
            }
            result.raw_result = tor_node
        else:
            result.details = "Not found."
        return result

    def parse_results(self, response: LookupResult) -> Tuple[bool, TISeverity, Any]:
        """
        Return the details of the response.

        Parameters
        ----------
        response : LookupResult
            The returned data response

        Returns
        -------
        Tuple[bool, TISeverity, Any]
            bool = positive or negative hit
            TISeverity = enumeration of severity
            Object with match details

        """
        return (True, TISeverity.information, None)
