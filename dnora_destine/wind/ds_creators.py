from dnora_destine.polytope_functions import download_ecmwf_from_destine

import xarray as xr
import numpy as np
from dnora.wind import Wind
import pandas as pd
from geo_skeletons.classes import Wind as PointWind

from dnora.read.ds_read_functions import setup_temp_dir
from dnora.type_manager.dnora_types import DnoraDataType


def ds_polytope_wind_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    lon: np.ndarray,
    lat: np.ndarray,
    **kwargs,
):

    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.WIND, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"

    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="165/166",
        end_time=end_time,
        lon=lon,
        lat=lat,
    )

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)

    # Represent original data that was downloaded
    orig_wind = PointWind.add_time()(
        lon=ds.u10.longitude.values,
        lat=ds.u10.latitude.values,
        time=(ds.time + ds.step).values,
    )
    orig_wind.set_u(ds.u10.values)
    orig_wind.set_v(ds.v10.values)

    # Represent new gridded data
    new_grid = Wind(lon=lon, lat=lat, time=orig_wind.time())
    new_grid.set_spacing(dlon=1 / 8, dlat=1 / 30)
    wind = orig_wind.resample.grid(new_grid)

    return wind.sel(time=slice(start_time, end_time)).ds()
