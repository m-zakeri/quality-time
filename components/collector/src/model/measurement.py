"""Measurement model classes."""

from typing import Optional, Sequence

from collector_utilities.type import ErrorMessage, Value, URL

from .entity import Entities


class SourceMeasurement:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Class to hold measurement values, entities, and error messages from collecting the measurement from a source."""

    MAX_ENTITIES = 100  # The maximum number of entities (e.g. violations, warnings) to send to the server

    def __init__(
        self, *, value: Value = None, total: Value = "100", entities: Entities = None, parse_error: ErrorMessage = None
    ) -> None:
        self.value = str(len(entities)) if value is None and entities is not None else value
        self.total = total
        self.entities = Entities() if entities is None else entities
        self.parse_error = parse_error
        self.connection_error: ErrorMessage = None
        self.api_url: Optional[URL] = None
        self.landing_url: Optional[URL] = None
        self.source_uuid: Optional[str] = None

    def has_error(self) -> bool:
        """Return whether the measurement had a connection or parse error."""
        return bool(self.connection_error or self.parse_error)

    def as_dict(self):
        """Return the source measurement as dict."""
        return dict(
            value=self.value,
            total=self.total,
            entities=self.entities[: self.MAX_ENTITIES],
            parse_error=self.parse_error,
            connection_error=self.connection_error,
            api_url=self.api_url,
            landing_url=self.landing_url,
            source_uuid=self.source_uuid,
        )


class MetricMeasurement:  # pylint: disable=too-few-public-methods
    """Class to hold measurements from one or more sources for one metric."""

    def __init__(self, sources: Sequence[SourceMeasurement]) -> None:
        self.sources = sources
        self.has_error = any(source.has_error() for source in sources)
        self.metric_uuid: Optional[str] = None

    def as_dict(self) -> dict:
        """Return the metric measurement as dict."""
        return dict(
            sources=[source.as_dict() for source in self.sources],
            has_error=self.has_error,
            metric_uuid=self.metric_uuid,
        )
