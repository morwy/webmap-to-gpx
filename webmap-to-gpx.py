#!/usr/bin/python

# --------------------------------------------------------------------------------------------------
#
# Imports.
#
# --------------------------------------------------------------------------------------------------
import logging
import os
import urllib.request
from dataclasses import dataclass

import chompjs  # type: ignore
import gpxpy  # type: ignore


# --------------------------------------------------------------------------------------------------
#
# Global variables.
#
# --------------------------------------------------------------------------------------------------
@dataclass
class Coordinate:
    latitude: int = 0
    longitude: int = 0


# --------------------------------------------------------------------------------------------------
#
# Class definition.
#
# --------------------------------------------------------------------------------------------------
class WebmapToGpx:

    @staticmethod
    def parse(url: str, timeout_seconds: int) -> None:
        logging.basicConfig(level=logging.DEBUG)

        page_name, line_data_dict = WebmapToGpx.__parse_web_sources(
            url=url, timeout_seconds=timeout_seconds
        )
        tracks = WebmapToGpx.__extract_tracks(line_data_dict)
        gpx = WebmapToGpx.__convert_to_gpx(tracks)
        WebmapToGpx.__save_gpx_to_file(page_name, gpx)

        logging.info("Done!")

    @staticmethod
    def __parse_web_sources(url: str, timeout_seconds: int):

        logging.info("Parsing '%s' webpage sources.", url)

        with urllib.request.urlopen(url=url, timeout=timeout_seconds) as webpage_handle:
            webpage_sources = str(webpage_handle.read().decode("utf8"))
            if len(webpage_sources) == 0:
                raise ValueError("No webpage sources were retrieved!")

            javascript_start_marker = '<script type="text/javascript">'
            if javascript_start_marker not in webpage_sources:
                raise ValueError(
                    "No javascript opening tag was found in webpage sources!"
                )

            javascript_end_marker = "</script>"
            if javascript_end_marker not in webpage_sources:
                raise ValueError(
                    "No javascript closing tag was found in webpage sources!"
                )

            webpage_parts = webpage_sources.split(javascript_start_marker)
            javascript_sources = webpage_parts[1].split(javascript_end_marker)[0]

            page_name = (
                javascript_sources.split("document.title = ")[1]
                .split(";")[0]
                .strip("'")
            )

            javascript_parts = javascript_sources.split("var lineData = ")
            line_data_raw = javascript_parts[1].split("var pointData = ")[0]
            line_data_dict = chompjs.parse_js_object(line_data_raw)

            logging.info(
                "Parsed %d waypoints.",
                len(line_data_dict["features"][0]["geometry"]["coordinates"]),
            )

            javascript_parts = javascript_sources.split("var pointData = ")
            point_data_raw = javascript_parts[1].split("var map = new maplibregl")[0]
            point_data_dict = chompjs.parse_js_object(point_data_raw)

            logging.info(
                "Parsed %d points of interest.",
                len(point_data_dict["features"]),
            )

        return page_name, line_data_dict

    @staticmethod
    def __extract_tracks(line_data_dict):
        logging.info("Creating list of tracks.")

        tracks: list = []

        for raw_track in line_data_dict["features"]:
            track: list = []

            if raw_track["geometry"]["type"] == "LineString":
                for coordinate in raw_track["geometry"]["coordinates"]:
                    track.append(
                        Coordinate(latitude=coordinate[1], longitude=coordinate[0])
                    )

                tracks.append(track)

            if raw_track["geometry"]["type"] == "MultiLineString":
                for line in raw_track["geometry"]["coordinates"]:
                    track = []

                    for coordinate in line:
                        track.append(
                            Coordinate(latitude=coordinate[1], longitude=coordinate[0])
                        )

                    tracks.append(track)

        logging.info("Parsed %d tracks.", len(tracks))

        return tracks

    @staticmethod
    def __convert_to_gpx(tracks):
        logging.info("Creating gpxpy object.")

        gpx = gpxpy.gpx.GPX()

        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        for track in tracks:
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for coordinate in track:
                gpx_segment.points.append(
                    gpxpy.gpx.GPXTrackPoint(coordinate.latitude, coordinate.longitude)
                )

        return gpx

    @staticmethod
    def __save_gpx_to_file(page_name, gpx):
        gpx_filename = page_name + ".gpx"
        logging.info("Exporting to '%s' file.", gpx_filename)

        current_script_folder_path = os.path.dirname(os.path.realpath(__file__))
        gpx_filepath = os.path.join(current_script_folder_path, gpx_filename)
        with open(file=gpx_filepath, mode="w", encoding="utf-8") as gpx_file:
            gpx_file.write(gpx.to_xml())


# --------------------------------------------------------------------------------------------------
#
# Entry point.
#
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    pass
