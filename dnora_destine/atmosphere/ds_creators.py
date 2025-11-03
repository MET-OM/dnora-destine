from dnora_destine.polytope_functions import download_ecmwf_from_destine

import xarray as xr
import numpy as np
from dnora.atmosphere import Atmosphere
import pandas as pd
from geo_skeletons import PointSkeleton
import geo_parameters as gp

from dnora.read.ds_read_functions import setup_temp_dir
from dnora.type_manager.dnora_types import DnoraDataType


def ds_polytope_atmosphere_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    lon: np.ndarray,
    lat: np.ndarray,
    **kwargs,
):

    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.ATMOSPHERE, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"

    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="151/167",
        end_time=end_time,
        lon=lon,
        lat=lat,
    )

    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)

    temp_file = f"{name}_temp2.grib"
    grib_file = f"{folder}/{temp_file}"

    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="157",
        end_time=end_time,
        lon=lon,
        lat=lat,
        levelist=1000,
    )

    ds2 = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)

    # Represent original data that was downloaded
    orig_data = (
        PointSkeleton.add_time()
        .add_datavar(gp.atm.MeanSeaLevelPressure("mslp"))
        .add_datavar(gp.atm.AirTemperature("t2m"))
        .add_datavar(gp.atm.RelativeHumidity("r"))(
            lon=ds.longitude.values,
            lat=ds.latitude.values,
            time=(ds.time + ds.step).values,
        )
    )

    orig_data.set_mslp(ds.msl.values)
    orig_data.set_t2m(ds.t2m.values)
    orig_data.set_r(ds2.r.values)
    # Represent new gridded data
    new_grid = Atmosphere(lon=lon, lat=lat, time=orig_data.time())
    new_grid.set_spacing(dlon=1 / 8, dlat=1 / 30)
    data = orig_data.resample.grid(new_grid)
    data.meta.append({"source": url})
    return data.sel(time=slice(start_time, end_time)).ds()
