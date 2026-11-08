"""Geometry helpers. Only numpy/scipy are required (no GIS libraries)."""
import numpy as np
from scipy.spatial import cKDTree

R_EARTH_KM = 6371.0088


def to_xyz(lon, lat):
    """Lon/lat (degrees) -> 3-D Cartesian km on a sphere.

    Euclidean (chord) distance between these points is within ~0.01% of the
    great-circle distance at the <=500 km scales used here.
    """
    lo = np.radians(np.asarray(lon, dtype=float))
    la = np.radians(np.asarray(lat, dtype=float))
    return R_EARTH_KM * np.column_stack(
        [np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    )


def local_xy(lon, lat, lon0=-76.0, lat0=40.5):
    """Approximate planar km coordinates (equirectangular). Used ONLY for
    spatial blocking and plotting, never for distance thresholds."""
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    return (lon - lon0) * 111.320 * np.cos(np.radians(lat0)), (lat - lat0) * 110.574


def nearest_distance(query_xyz, ref_xyz):
    """Distance (km) from each query point to its nearest reference point."""
    query_xyz = np.asarray(query_xyz, dtype=float)
    ref_xyz = np.asarray(ref_xyz, dtype=float)
    if len(ref_xyz) == 0:
        return np.full(len(query_xyz), np.inf)
    d, _ = cKDTree(ref_xyz).query(query_xyz, k=1)
    return d


def gaussian_kde_at(target_xyz, source_xyz, source_weight, bandwidth_km):
    """sum_j w_j * exp(-d_ij^2 / (2 h^2)) at each target point (km units).

    Sources farther than 4h are ignored (kernel value < 3.4e-4).
    """
    target_xyz = np.asarray(target_xyz, dtype=float)
    source_xyz = np.asarray(source_xyz, dtype=float)
    n = len(target_xyz)
    if len(source_xyz) == 0 or n == 0:
        return np.zeros(n)
    h = float(bandwidth_km)
    rec = cKDTree(target_xyz).sparse_distance_matrix(
        cKDTree(source_xyz), 4.0 * h, output_type="ndarray"
    )
    if len(rec) == 0:
        return np.zeros(n)
    w = np.asarray(source_weight, dtype=float)[rec["j"]]
    vals = w * np.exp(-0.5 * (rec["v"] / h) ** 2)
    return np.bincount(rec["i"], weights=vals, minlength=n)
