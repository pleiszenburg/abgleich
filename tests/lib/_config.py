from typing import Iterator, List, Optional, Tuple

from yaml import dump
from typeguard import typechecked

from ._repr import repr_tree


@typechecked
class Apool:
    """
    represent a section of a zpool for abgleich to handle
    """

    def __init__(
        self,
        alias: str,
        root: str,
        user: Optional[str] = None,
        route: Tuple[str, ...] = ("localhost",),
    ):
        """
        init
        """

        self._alias = alias
        self._root = root
        self._user = user
        self._route = route

    def __repr__(self) -> str:
        """
        interactive representation
        """

        user = "" if self._user is None else f" user={self._user:s}"
        return f"<Apool route={'/'.join(self._route):s}{user:s} root={self._root:s}>"

    @property
    def alias(self) -> str:
        """
        alias
        """

        return self._alias

    @property
    def route(self) -> Tuple[str, ...]:
        """
        route
        """

        return self._route

    def to_serializable(self) -> str:
        """
        to serializable data
        """

        user = "" if self._user is None else f"{self._user:s}%"
        return f"{'/'.join(self._route):s}:{user:s}{self._root:s}"


@typechecked
class Config:
    """
    represents configuration of abgleich for testing
    """

    def __init__(
        self,
        apools: Optional[List[Apool]] = None,
    ):
        """
        init
        """

        self._apools = {} if apools is None else {apool.alias: apool for apool in apools}

    def __repr__(self) -> str:
        """
        interactive representation
        """

        return repr_tree(
            base = "<Config>",
            branches = self._apools,
        )

    def __contains__(self, alias) -> bool:
        """
        does config contain apool
        """

        return alias in self._apools.keys()

    def __getitem__(self, alias: str) -> Apool:
        """
        access apool by alias
        """

        return self._apools[alias]

    @property
    def aliases(self) -> Iterator[str]:
        """
        all aliases
        """

        return (apool.alias for apool in self._apools.values())

    @property
    def apools(self) -> Iterator[Apool]:
        """
        all aliases
        """

        return (apool for apool in self._apools.values())

    def to_raw(self) -> str:
        """
        to plain text that can be written to file
        """

        return dump(self.to_serializable())

    def to_serializable(self) -> dict:
        """
        to serializable data
        """

        return dict(
            apools = {
                alias: apool.to_serializable()
                for alias, apool in self._apools.items()
            },
        )
