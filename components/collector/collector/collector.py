"""Collector base class."""

import itertools
import logging
import traceback
import urllib.parse
from typing import cast, Optional, Set, Tuple, Type

import cachetools
import requests

from .type import ErrorMessage, Measurement, Measurements, Response, URL


class Collector:
    """Base class for metric collectors."""

    TIMEOUT = 10  # Default timeout of 10 seconds
    RESPONSE_CACHE = cachetools.TTLCache(maxsize=256, ttl=60)  # Briefly cache responses to prevent flooding sources
    subclasses: Set[Type["Collector"]] = set()
    name = "Subclass responsibility"

    def __init__(self, request_url: URL) -> None:
        self.request_url = request_url
        url_parts = urllib.parse.urlsplit(request_url)
        self.query = urllib.parse.parse_qs(url_parts.query)

    def __init_subclass__(cls) -> None:
        Collector.subclasses.add(cls)
        super().__init_subclass__()

    @classmethod
    def get_subclass(cls, source_and_metric: str) -> Type["Collector"]:
        """Return the subclass registered for the source/metric name."""
        simplified_class_name = source_and_metric.replace("_", "")
        matching_subclasses = [sc for sc in cls.subclasses if sc.__name__.lower() == simplified_class_name]
        return matching_subclasses[0] if matching_subclasses else cls

    def get(self) -> Response:
        """Connect to the sources to get and parse the measurement for the metric."""
        metric_name = urllib.parse.urlsplit(self.request_url).path.strip("/")
        sources = self.query.get("source", [])
        urls = self.query.get("url", [])
        components = self.query.get("component", [])
        source_responses = []
        for source, url, component in itertools.zip_longest(sources, urls, components, fillvalue=""):
            collector_class = cast(Type[Collector], Collector.get_subclass(f"{source}_{metric_name}"))
            source_collector = collector_class(self.request_url)
            source_responses.append(source_collector.get_one(url, component))

        measurements = [source_response["measurement"] for source_response in source_responses]
        measurement, calculation_error = self.safely_sum(measurements)
        return dict(
            measurement=dict(calculation_error=calculation_error, measurement=measurement),
            sources=source_responses,
            request=dict(
                request_url=self.request_url, metric=metric_name, sources=sources, urls=urls, components=components))

    def get_one(self, url: URL, component: str) -> Response:
        """Return the measurement response for one source url."""
        api_url = self.api_url(url, component)
        landing_url = self.landing_url(url, component)
        response, connection_error = self.safely_get_source_response(api_url)
        measurement, parse_error = self.safely_parse_source_response(response) if response else (None, None)
        return dict(name=self.name, api_url=api_url, landing_url=landing_url, measurement=measurement,
                    connection_error=connection_error, parse_error=parse_error)

    def landing_url(self, url: URL, component: str) -> URL:  # pylint: disable=unused-argument,no-self-use
        """Translate the urls into the landing urls."""
        return url

    def api_url(self, url: URL, component: str) -> URL:  # pylint: disable=unused-argument,no-self-use
        """Translate the url into the API url."""
        return url

    @cachetools.cached(RESPONSE_CACHE, key=lambda self, url: cachetools.keys.hashkey(url))
    def safely_get_source_response(self, url: URL) -> Tuple[Optional[requests.Response], Optional[ErrorMessage]]:
        """Connect to the source and get the data, without failing."""
        response, error = None, None
        try:
            response = self.get_source_response(url)
        except Exception:  # pylint: disable=broad-except
            error = ErrorMessage(traceback.format_exc())
        return response, error

    def get_source_response(self, url: URL) -> requests.Response:
        """Open the url. Raise an exception if the response status isn't 200 or if a time out occurs."""
        logging.info("Retrieving %s", url)
        response = requests.get(url, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response

    def safely_parse_source_response(self, response: requests.Response) -> \
            Tuple[Optional[Measurement], Optional[ErrorMessage]]:
        """Parse to the measurement from the response, without failing."""
        measurement, error = None, None
        try:
            measurement = self.parse_source_response(response)
        except Exception:  # pylint: disable=broad-except
            error = ErrorMessage(traceback.format_exc())
        return measurement, error

    def parse_source_response(self, response: requests.Response) -> Measurement:
        # pylint: disable=no-self-use
        """Parse the response to get the measurement for the metric."""
        return Measurement(response.text)

    def safely_sum(self, measurements: Measurements) -> Tuple[Optional[Measurement], Optional[ErrorMessage]]:
        """Return the summation of several measurements, without failing."""
        measurement, error = None, None
        if measurements and None not in measurements:
            if len(measurements) > 1:
                try:
                    measurement = self.sum(measurements)
                except Exception:  # pylint: disable=broad-except
                    error = ErrorMessage(traceback.format_exc())
            else:
                measurement = measurements[0]
        return measurement, error

    def sum(self, measurements: Measurements) -> Measurement:  # pylint: disable=no-self-use
        """Return the summation of several measurements."""
        return Measurement(sum(int(measurement) for measurement in measurements))