"""OPTIONAL: extract raster covariates (climate, elevation, population density, ...)
at the lyde 10-km cell centroids and write covariates.csv for run_real.py.

Raster reading uses Pillow (pip install pillow) with an automatic fallback to
rasterio (pip install rasterio) if Pillow cannot decode a file. Values are the
mean of all raster pixels inside a square window (default 10 km x 10 km) centred
on each cell centroid.

Usage
-----
    python -m slf_effort.covariates --lyde lyde.csv --out covariates.csv \
        --raster bio1=wc2.1_10m_bio_1.tif --raster bio12=wc2.1_10m_bio_12.tif \
        --raster logpop=usa_pd_2020_1km.tif:log1p

    python -m slf_effort.covariates --selftest          # checks the reader on a synthetic GeoTIFF

Rasters must be in geographic coordinates (EPSG:4326, e.g. WorldClim, WorldPop).
"""
import argparse
import os
import sys
import tempfile

import numpy as np
import pandas as pd


class GeoRaster:
    def __init__(self, path):
        self.path = path
        last = None
        for reader in (self._read_pil, self._read_rasterio):
            try:
                reader(path)
                return
            except Exception as e:          # try the next reader
                last = e
        raise RuntimeError(f"Could not read {path} as a geographic GeoTIFF: {last}\n"
                           "Install Pillow (pip install pillow) and/or rasterio (pip install rasterio).")

    def _set(self, arr, x0, y0, dx, dy, nodata):
        arr = np.asarray(arr, dtype="float64")
        bad = ~np.isfinite(arr) | (arr < -1e30)
        if nodata is not None and np.isfinite(nodata):
            bad |= np.isclose(arr, nodata)
        arr[bad] = np.nan
        self.arr, self.x0, self.y0, self.dx, self.dy = arr, float(x0), float(y0), float(dx), float(dy)

    def _read_pil(self, path):
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(path)
        tags = im.tag_v2
        scale, tie = tags.get(33550), tags.get(33922)
        if scale is None or tie is None:
            raise ValueError("no GeoTIFF ModelPixelScale/ModelTiepoint tags")
        nod = tags.get(42113)
        try:
            nodata = float(str(nod).strip("\x00 ")) if nod is not None else None
        except ValueError:
            nodata = None
        arr = np.array(im, dtype="float64")
        if arr.ndim != 2:
            raise ValueError("expected a single-band raster")
        x0 = tie[3] - tie[0] * scale[0]
        y0 = tie[4] + tie[1] * scale[1]
        self._set(arr, x0, y0, scale[0], scale[1], nodata)

    def _read_rasterio(self, path):
        import rasterio
        with rasterio.open(path) as src:
            arr = src.read(1)
            t = src.transform
            self._set(arr, t.c, t.f, t.a, -t.e, src.nodata)

    def window_mean(self, lon, lat, half_km):
        dlat = half_km / 110.574
        dlon = half_km / (111.320 * np.cos(np.radians(lat)))
        h, w = self.arr.shape
        c0 = int(np.floor((lon - dlon - self.x0) / self.dx))
        c1 = int(np.floor((lon + dlon - self.x0) / self.dx))
        r0 = int(np.floor((self.y0 - (lat + dlat)) / self.dy))
        r1 = int(np.floor((self.y0 - (lat - dlat)) / self.dy))
        c0, c1, r0, r1 = max(c0, 0), min(c1, w - 1), max(r0, 0), min(r1, h - 1)
        if c0 > c1 or r0 > r1:
            return np.nan
        win = self.arr[r0:r1 + 1, c0:c1 + 1]
        return float(np.nanmean(win)) if np.isfinite(win).any() else np.nan


def unique_cells(lyde_path):
    d = pd.read_csv(lyde_path, usecols=["rounded_longitude_10k", "rounded_latitude_10k"])
    d = d.dropna().round(5).drop_duplicates().rename(
        columns={"rounded_longitude_10k": "lon", "rounded_latitude_10k": "lat"})
    return d.reset_index(drop=True)


def extract(cells, specs, half_km=5.0):
    out = cells.copy()
    for spec in specs:
        name, rest = spec.split("=", 1)
        path, _, transform = rest.partition(":")
        r = GeoRaster(path)
        vals = np.array([r.window_mean(lo, la, half_km) for lo, la in zip(cells["lon"], cells["lat"])])
        if transform == "log1p":
            vals = np.log1p(np.clip(vals, 0, None))
        elif transform not in ("", "none"):
            raise ValueError(f"unknown transform '{transform}' (use log1p or none)")
        out[name] = vals
        print(f"  {name}: {np.isfinite(vals).mean() * 100:.1f}% of cells have values; "
              f"min/median/max = {np.nanmin(vals):.3g} / {np.nanmedian(vals):.3g} / {np.nanmax(vals):.3g}")
    return out


def selftest():
    from PIL import Image, TiffImagePlugin
    with tempfile.TemporaryDirectory() as td:
        h, w = 200, 300                       # 0.05-degree pixels over lon -80..-65, lat 45..35
        x0, y0, dx, dy = -80.0, 45.0, 0.05, 0.05
        lon = x0 + (np.arange(w) + 0.5) * dx
        lat = y0 - (np.arange(h) + 0.5) * dy
        grid = (lon[None, :] + 100.0) * 10.0 + lat[:, None]       # smooth, known function
        grid[:5, :5] = -3.4e38                                    # nodata corner
        im = Image.fromarray(grid.astype("float32"), mode="F")
        info = TiffImagePlugin.ImageFileDirectory_v2()
        info[33550] = (dx, dy, 0.0)
        info[33922] = (0.0, 0.0, 0.0, x0, y0, 0.0)
        p = os.path.join(td, "synthetic.tif")
        im.save(p, tiffinfo=info, compression="tiff_lzw")
        r = GeoRaster(p)
        assert abs(r.x0 - x0) < 1e-9 and abs(r.y0 - y0) < 1e-9, (r.x0, r.y0)
        v = r.window_mean(-75.0, 40.0, 1.0)
        expect = (-75.0 + 100.0) * 10.0 + 40.0
        assert abs(v - expect) < 0.5, (v, expect)
        assert np.isnan(r.window_mean(-79.9, 44.9, 1.0)), "nodata corner should be NaN"
        assert np.isnan(r.window_mean(-10.0, 40.0, 1.0)), "outside raster should be NaN"
        cells = pd.DataFrame({"lon": [-75.0, -70.0], "lat": [40.0, 38.0]})
        out = extract(cells, [f"v={p}", f"lv={p}:log1p"])
        assert abs(out["v"][1] - ((-70.0 + 100) * 10 + 38.0)) < 0.5
        assert np.isclose(out["lv"][0], np.log1p(out["v"][0]))
    print("covariates selftest: PASS (Pillow GeoTIFF reader, window mean, nodata, log1p)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lyde")
    ap.add_argument("--out", default="covariates.csv")
    ap.add_argument("--raster", action="append", default=[], help="name=path[:log1p]  (repeatable)")
    ap.add_argument("--half-km", type=float, default=5.0, help="half window width in km (5 = 10 km cell)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return
    if not a.lyde or not a.raster:
        ap.error("need --lyde and at least one --raster name=path (or --selftest)")
    cells = unique_cells(a.lyde)
    print(f"{len(cells)} cells; extracting {len(a.raster)} raster(s)")
    out = extract(cells, a.raster, a.half_km)
    out.to_csv(a.out, index=False)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
