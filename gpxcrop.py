#!/usr/bin/env python3

# ./gpxcrop test.gpx 90,180,45,-180

import sys
import xml.dom.minidom

def line_segment_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    """
    Compute line segment intersection.

    Line 1: (x1, y1) to (x2, y2)
    Line 2: (x3, y3) to (x4, y4)

    returns intersection (px, py)

    returns None with no intersection.

    https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
    """

    # Common divisor
    print(x1, y1, x2, y2, x3, y3, x4, y4, file=sys.stderr)
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    # Check for parallel lines
    if d == 0:
        return None

    # Make sure we're not off the end of segment 1
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d

    if t < 0 or t > 1:
        return None

    # Make sure we're not off the end of segment 2
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / d

    if u < 0 or u > 1:
        return None

    # Common other factors
    f1 = x1*y2 - y1*x2
    f2 = x3*y4 - y3*x4

    # Intersection
    px = (f1 * (x3 - x4) - (x1 - x2) * f2) / d
    py = (f1 * (y3 - y4) - (y1 - y2) * f2) / d

    return px, py

def usage():
    """
    Print a usage message.
    """

    print("usage: gpxcrop file.gpx lat0,lon0,lat1,lon1", file=sys.stderr)

def normalize_coords(corners):
    """
    Make sure lat0, lon0 is in the upper left.
    """

    lat0, lon0, lat1, lon1 = corners

    if lat1 < lat0: lat0, lat1 = lat1, lat0
    if lon1 < lon0: lon0, lon1 = lon1, lon0

    corners[0] = lat0
    corners[1] = lon0
    corners[2] = lat1
    corners[3] = lon1

def in_bounds(lat, lon, corners):
    """
    Return true if the lat lon is within the corners.
    """
    return \
        lat >= corners[0] and lat <= corners[2] and \
        lon >= corners[1] and lon <= corners[3]

def get_crop_point(lat, lon, plat, plon, corners):
    """
    Compute the intersection between a line segment and the bounding
    box. Return None if no intersection.
    """

    # corners[0], corners[1]      corners[2], corners[1]
    #
    # corners[0], corners[3]      corners[2], corners[3]

    r = line_segment_intersect(lat, lon, plat, plon, corners[0], corners[1], corners[0], corners[3])
    if r is not None: return r

    r = line_segment_intersect(lat, lon, plat, plon, corners[0], corners[3], corners[2], corners[3])
    if r is not None: return r

    r = line_segment_intersect(lat, lon, plat, plon, corners[2], corners[3], corners[2], corners[1])
    if r is not None: return r

    r = line_segment_intersect(lat, lon, plat, plon, corners[2], corners[1], corners[0], corners[1])
    if r is not None: return r

    return None

def crop_segments(new_trk, trk, corners):
    """
    Crop all the track segments to a bounding box.

    Make new segments as necessary.

    Interpolate the intersection points between the line segments and
    bounding box.
    """

    new_seg = None
    in_crop = False

    for trkseg in trk.getElementsByTagName('trkseg'):
        plat = None
        plon = None

        for trkpt in trkseg.getElementsByTagName('trkpt'):
            lat = float(trkpt.getAttribute("lat"))
            lon = float(trkpt.getAttribute("lon"))

            new_in_crop = in_bounds(lat, lon, corners)

            # Transition out
            if in_crop and not new_in_crop:
                if plat is not None:
                    cx, cy = get_crop_point(lat, lon, plat, plon, corners)

                    new_trkpt = trkpt.cloneNode(False)
                    new_trkpt.setAttribute("lat", str(cx))
                    new_trkpt.setAttribute("lon", str(cy))
                    new_seg.appendChild(new_trkpt)

                if len(new_seg.childNodes) > 0:
                    new_trk.appendChild(new_seg)

                in_crop = False
                new_seg = None

            # Transition in
            elif not in_crop and new_in_crop:
                new_seg = trkseg.cloneNode(False)

                if plat is not None:
                    cx, cy = get_crop_point(lat, lon, plat, plon, corners)

                    new_trkpt = trkpt.cloneNode(False)
                    new_trkpt.setAttribute("lat", str(cx))
                    new_trkpt.setAttribute("lon", str(cy))
                    new_seg.appendChild(new_trkpt)

                in_crop = True

            if in_crop:
                trkseg.removeChild(trkpt)
                new_seg.appendChild(trkpt)
                #print(f'appending {lat} {lon}')

            plat = lat
            plon = lon

        if new_seg is not None and len(new_seg.childNodes) > 0:
            new_trk.appendChild(new_seg)

def crop_tracks(gpxnode, foster, corners):
    """
    Go through all tracks, and call crop_segments() to split segments
    up.
    """
    for trk in foster.getElementsByTagName('trk'):
        new_trk = trk.cloneNode(False)

        # Go through all track segments and split them up
        crop_segments(new_trk, trk, corners)

        if len(new_trk.childNodes) > 0:

            # Copy all the non-trkseg nodes over
            # Find the first node to insert before
            first = None

            for c in new_trk.childNodes:
                if c.nodeType == xml.dom.Node.ELEMENT_NODE:
                    first = c
                    break

            # Find all the non-trkseg nodes
            for c in trk.childNodes:
                if c.nodeType == xml.dom.Node.ELEMENT_NODE and \
                   c.tagName.lower() != 'trkseg':

                    new_c = c.cloneNode(True)
                    new_trk.insertBefore(new_c, first)

            # Fully cooked, append the new track
            gpxnode.appendChild(new_trk)

def main(argv):
    """
    Main.
    """
    if len(argv) != 3:
        usage()
        return 1

    try:
        corners = list(map(float, argv[2].split(',')))
    except ValueError:
        usage()
        return 1

    if len(corners) != 4:
        usage()
        return 1

    normalize_coords(corners)

    gpxdom = xml.dom.minidom.parse(argv[1])
    gpxnode = gpxdom.documentElement

    # Move tracks into a foster parent and out of the main dom
    foster = gpxnode.cloneNode(False)

    for trk in gpxnode.getElementsByTagName('trk'):
        gpxnode.removeChild(trk)
        foster.appendChild(trk)

    # Go through the tracks on the foster parent and append them back
    # into the main dom
    crop_tracks(gpxnode, foster, corners)

    # Output final dom
    print(gpxdom.toprettyxml())

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
