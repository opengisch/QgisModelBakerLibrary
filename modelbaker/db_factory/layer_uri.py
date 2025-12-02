"""
Metadata:
    Creation Date: 2019-04-30
    Copyright: (C) 2019 by Yesid Polania
    Contact: yesidpol.3@gmail.com

License:
    This program is free software; you can redistribute it and/or modify
    it under the terms of the **GNU General Public License** as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""

from abc import ABC, abstractmethod


class LayerUri(ABC):
    """Provides layer uri based on database uri (connection string) and specific information of the data source. This is a abstract class.

    This **layer uri** is used to create a Qgis layer.
    """

    def __init__(self, uri: str) -> None:
        """

        Args:
            uri (str): Database uri. This is the same database uri of the db connectors."""
        self.uri = uri
        self.provider = None

    @abstractmethod
    def get_data_source_uri(self, record: dict) -> str:
        """Provides layer uri based on database uri and specific information of the data source.

        Args:
            record (str): Dictionary containing specific information of the data source.

        Returns:
            str: Layer uri."""
