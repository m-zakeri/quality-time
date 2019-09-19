"""Unit tests for the data model."""

import json
import unittest


class DataModelTest(unittest.TestCase):
    """Unit tests for the data model."""

    def setUp(self):
        with open("src/data/datamodel.json") as datamodel_json:
            self.datamodel = json.load(datamodel_json)

    def test_top_level_keys(self):
        """Test that the top level keys are correct."""
        self.assertEqual({"metrics", "subjects", "sources"}, set(self.datamodel.keys()))

    def test_metrics_have_sources(self):
        """Test that each metric has one or more sources."""
        for metric in self.datamodel["metrics"].values():
            self.assertTrue(len(metric["sources"]) >= 1)

    def test_source_parameter_metrics(self):
        """Test that the metrics listed for source parameters are metrics supported by the source."""
        for source_id, source in self.datamodel["sources"].items():
            for parameter in source["parameters"].values():
                for metric in parameter["metrics"]:
                    self.assertTrue(source_id in self.datamodel["metrics"][metric]["sources"])

    def test_metric_source_parameters(self):
        """Test that the sources have at least one parameter for each metric supported by the source."""
        for metric_id, metric in self.datamodel["metrics"].items():
            for source in metric["sources"]:
                parameters = self.datamodel["sources"][source]["parameters"]
                if not parameters:
                    continue
                parameter_metrics = []
                for parameter in parameters.values():
                    parameter_metrics.extend(parameter["metrics"])
                self.assertTrue(
                    metric_id in parameter_metrics, f"No parameters for metric '{metric_id}' in source '{source}'")

    def test_multiple_choice_parameters(self):
        """Test that multiple choice parameters have both a default value and a list of options."""
        for source in self.datamodel["sources"].values():
            for parameter in source["parameters"].values():
                if parameter["type"] == "multiple_choice":
                    self.assertTrue("default_value" in parameter)
                    self.assertTrue("values" in parameter)

    def test_addition(self):
        """Test each metric had its addition defined correctly."""
        for metric in self.datamodel["metrics"].values():
            self.assertTrue(metric["addition"] in ("max", "min", "sum"))

    def test_mandatory_parameters(self):
        """Test that each metric has a mandatory field with true or false value."""
        for source_id, source in self.datamodel["sources"].items():
            for parameter_id, parameter_values in source["parameters"].items():
                self.assertTrue(
                    "mandatory" in parameter_values,
                    f"The parameter '{parameter_id}' of source '{source_id}' has no 'mandatory' field")
                self.assertTrue(
                    parameter_values["mandatory"] in (True, False),
                    f"The 'mandatory' field of parameter '{parameter_id}' of source '{source_id}' is neither "
                    "true nor false")

    def test_default_source(self):
        """Test that each metric has a default source, and that the default source is listed as possible source."""
        for metric in self.datamodel["metrics"].values():
            self.assertTrue(metric["default_source"] in metric["sources"])

    def test_entity_attributes(self):
        """Test that entities have the required attributes."""
        for source_id, source in self.datamodel["sources"].items():
            for entity_key, entity_value in source["entities"].items():
                self.assertTrue("name" in entity_value.keys())
                self.assertTrue("name_plural" in entity_value.keys(), f"No 'name_plural' in {source_id}.{entity_key}")

    def test_colors(self):
        """Test that the color values are correct."""
        for source_id, source in self.datamodel["sources"].items():
            for entity_key, entity_value in source["entities"].items():
                for attribute in entity_value["attributes"]:
                    for color_value in attribute.get("color", {}).values():
                        self.assertTrue(
                            color_value in ("active", "error", "negative", "positive", "warning"),
                            f"Color {color_value} of {source_id}.{entity_key} is not correct")

    def test_metrics_belong_to_at_least_one_subject(self):
        """Test that each metric belongs to at least one subject."""
        for metric in self.datamodel["metrics"]:
            for subject in self.datamodel["subjects"].values():
                if metric in subject["metrics"]:
                    break
            else:  # pragma: nocover
                self.fail(f"Metric {metric} not listed in any subject.")

    def test_hq_parameters(self):
        """Test that the HQ parameters URL and metric id support the same metrics."""
        hq_parameters = self.datamodel["sources"]["hq"]["parameters"]
        self.assertEqual(hq_parameters["url"]["metrics"], hq_parameters["metric_id"]["metrics"])

    def test_sources_with_landing_url(self):
        """Test that the the sources with landing url also have url."""
        for source in self.datamodel["sources"]:
            if "landing_url" in self.datamodel["sources"][source]["parameters"]:
                self.assertTrue("url" in self.datamodel["sources"][source]["parameters"],
                                 f"Source >{source}< has a landing url parameter, but not url.")

    def test_metric_direction(self):
        """Test that all metrics have a valid direction."""
        for metric_uuid, metric in self.datamodel["metrics"].items():
            direction = metric["direction"]
            self.assertTrue(direction in ("<", ">"), f"Metric {metric_uuid} has an invalid direction: {direction}")
