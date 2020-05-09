# GPX cropping tool

This is a half-baked thing that I was going to use, but then didn't.

But it works, generally.

A track will have additional track segments added to it as necessary
(i.e. if the track segment exits and reenters the bounding box.)

## Usage

Specify an input GPX, a lat/lon bounding box, and redirect the output
into the outfile.

```
gpxcrop.py infile.gpx lat0,lon0,lat1,lon1 > outfile.gpx
```

## TODO

* `setup.py` and packaging.
* Options for preserving/removing waypoints
* Options for also cropping waypoints
* Specify output file
* Track point metadata interpolation
  * When cropping, new points are introduced. These could be loaded up
    with elevation and timestamp information, linearly interpolated at
    the crop point.

## Contact

Brian "Beej" Hall

[beej@beej.us](mailto:beej@beej.us)
