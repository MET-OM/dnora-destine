from dnora_destine.polytope_functions import download_ecmwf_from_destine

import xarray as xr
import numpy as np
from dnora.ice import Ice
import pandas as pd
from geo_skeletons import PointSkeleton
import geo_parameters as gp

from dnora.read.ds_read_functions import setup_temp_dir
from dnora.type_manager.dnora_types import DnoraDataType


def ds_polytope_ice_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    lon: np.ndarray,
    lat: np.ndarray,
    **kwargs,
):

    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.ICE, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"

    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="31",
        end_time=end_time,
        lon=lon,
        lat=lat,
    )

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)

    # Represent original data that was downloaded
    orig_ice = PointSkeleton.add_time().add_datavar(gp.ocean.IceFraction("sic"))(
        lon=ds.siconc.longitude.values,
        lat=ds.siconc.latitude.values,
        time=(ds.time + ds.step).values,
    )
    orig_ice.set_sic(ds.siconc.values)
    # Represent new gridded data
    new_grid = Ice(lon=lon, lat=lat, time=orig_ice.time())
    new_grid.set_spacing(dlon=1 / 8, dlat=1 / 30)
    ice = orig_ice.resample.grid(new_grid)

    return ice.sel(time=slice(start_time, end_time)).ds()
