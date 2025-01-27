from datetime import datetime, timezone


def save_track_as_little_r(filename, cyclone_data):
    """
    Convert and save cyclone data in little_R format.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for cyclone_id, tracks in cyclone_data.items():
            for track in tracks:
                # Parse the time
                dt = datetime.fromisoformat(track['time'].replace('Z', '+00:00'))

                # Header line 1
                header1 = f"{float(track['latitude']):20.5f}{float(track['longitude']):20.5f}{'HMS':40}"
                header1 += f"{0:10d}{0:10d}{0:10d}"  # Station ID numbers
                header1 += f"{dt.year:10d}{dt.month:10d}{dt.day:10d}{dt.hour:10d}{0:10d}"
                header1 += f"{0:10d}{0:10.3f}{cyclone_id:40}"
                f.write(header1 + '\n')

                # Header line 2
                header2 = f"{0:20.5f}{1:10d}{0:10.3f}"
                f.write(header2 + '\n')

                # Data line format: p, z, t, d, s, d (pressure, height, temp, dewpoint, speed, direction)
                # We'll only include position data
                data_line = f"{-888888.0:13.5f}{float(track['latitude']):13.5f}{-888888.0:13.5f}"
                data_line += f"{-888888.0:13.5f}{-888888.0:13.5f}{float(track['longitude']):13.5f}"
                data_line += f"{0:7d}"  # End of data line marker
                f.write(data_line + '\n')

                # End of record line
                f.write(f"{-777777.0:13.5f}\n")

    print("Saved to", filename)


def save_track_as_kml(filename, cyclone_data):
    """
    Convert and save cyclone data as KML, handling meridian crossing.
    """
    kml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n'

    for cyclone_id, tracks in cyclone_data.items():
        kml += f'  <Placemark>\n    <name>{cyclone_id}</name>\n    <MultiGeometry>\n'

        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                kml += '      <LineString>\n        <coordinates>\n'
                coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                               for track in current_segment]
                kml += '\n'.join(coordinates)
                kml += '\n        </coordinates>\n      </LineString>\n'

                # Start new segment
                current_segment = [tracks[i]]
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            kml += '      <LineString>\n        <coordinates>\n'
            coordinates = [f'          {track["longitude"]},{track["latitude"]},{0}'
                           for track in current_segment]
            kml += '\n'.join(coordinates)
            kml += '\n        </coordinates>\n      </LineString>\n'

        kml += '    </MultiGeometry>\n  </Placemark>\n'

    kml += '</Document>\n</kml>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(kml)
    print(f"Saved to {filename}")


def save_track_as_gpx(filename, cyclone_data):
    """Convert and save cyclone data as GPX, handling meridian crossing."""
    gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx += '<gpx version="1.1" creator="Windborne" xmlns="http://www.topografix.com/GPX/1/1">\n'

    for cyclone_id, tracks in cyclone_data.items():
        gpx += f'  <trk>\n    <name>{cyclone_id}</name>\n'

        current_segment = []
        segment_count = 1

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append(tracks[i])
                continue

            prev_lon = float(current_segment[-1]['longitude'])

            # Check if we've crossed the meridian
            if abs(lon - prev_lon) > 180:
                # Write the current segment
                gpx += '    <trkseg>\n'
                for point in current_segment:
                    gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                    gpx += f'        <time>{point["time"]}</time>\n'
                    gpx += '      </trkpt>\n'
                gpx += '    </trkseg>\n'

                # Start new segment
                current_segment = [tracks[i]]
                segment_count += 1
            else:
                current_segment.append(tracks[i])

        # Write the last segment if it's not empty
        if current_segment:
            gpx += '    <trkseg>\n'
            for point in current_segment:
                gpx += f'      <trkpt lat="{point["latitude"]}" lon="{point["longitude"]}">\n'
                gpx += f'        <time>{point["time"]}</time>\n'
                gpx += '      </trkpt>\n'
            gpx += '    </trkseg>\n'

        gpx += '  </trk>\n'

    gpx += '</gpx>'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(gpx)
    print(f"Saved to {filename}")


def save_track_as_geojson(filename, cyclone_data):
    """Convert and save cyclone data as GeoJSON, handling meridian crossing."""
    features = []
    for cyclone_id, tracks in cyclone_data.items():
        # Initialize lists to store line segments
        line_segments = []
        current_segment = []

        for i in range(len(tracks)):
            lon = float(tracks[i]['longitude'])
            lat = float(tracks[i]['latitude'])

            if not current_segment:
                current_segment.append([lon, lat])
                continue

            prev_lon = current_segment[-1][0]

            # Check if we've crossed the meridian (large longitude jump)
            if abs(lon - prev_lon) > 180:
                # If previous longitude was positive and current is negative
                if prev_lon > 0 and lon < 0:
                    # Add point at 180° with same latitude
                    current_segment.append([180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at -180°
                    current_segment = [[-180, lat], [lon, lat]]
                # If previous longitude was negative and current is positive
                elif prev_lon < 0 and lon > 0:
                    # Add point at -180° with same latitude
                    current_segment.append([-180, lat])
                    line_segments.append(current_segment)
                    # Start new segment at 180°
                    current_segment = [[180, lat], [lon, lat]]
            else:
                current_segment.append([lon, lat])

        # Add the last segment if it's not empty
        if current_segment:
            line_segments.append(current_segment)

        # Create a MultiLineString feature with all segments
        feature = {
            "type": "Feature",
            "properties": {
                "cyclone_id": cyclone_id,
                "start_time": tracks[0]['time'],
                "end_time": tracks[-1]['time']
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": line_segments
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=4)
    print("Saved to", filename)

