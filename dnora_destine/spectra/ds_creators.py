from dnora_destine.polytope_functions import download_ecmwf_from_destine

import xarray as xr
import numpy as np
from dnora.spectra import Spectra
import pandas as pd

from dnora.read.ds_read_functions import setup_temp_dir
from dnora.type_manager.dnora_types import DnoraDataType
from dnora import msg
from dnora import utils


def ds_polytope_spectra_read(
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    url: str,
    ## Partial variables from ProductReader
    inds: list[int],
    ## Partial variables in ProductConfiguration
    freq0: float,
    nfreq: int,
    finc: float,
    ndirs: int,
    **kwargs,
):
    name = "ECMWF"
    folder = setup_temp_dir(DnoraDataType.SPECTRA, name)

    temp_file = f"{name}_temp.grib"
    grib_file = f"{folder}/{temp_file}"
    download_ecmwf_from_destine(
        start_time=start_time,
        url=url,
        out_file=grib_file,
        params="140229/140230/140231",
        end_time=end_time,
    )
    ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
    ds = ds.isel(values=inds)
    ii = np.where(
        np.logical_and(
            ds.valid_time.values >= start_time, ds.valid_time.values <= end_time
        )
    )[0]
    ds = ds.isel(step=ii)
    msg.plain("Calculating JONSWAP spectra with given Hs and Tp...")
    fp = 1 / ds.pp1d.values
    m0 = ds.swh.values**2 / 16

    freq = np.array([freq0 * finc**n for n in np.linspace(0, nfreq - 1, nfreq)])
    dD = 360 / ndirs
    dirs = np.linspace(0, 360 - dD, ndirs)
    E = utils.spec.jonswap1d(fp=fp, m0=m0, freq=freq)

    msg.plain("Expanding to cos**2s directional distribution around mean direction...")
    Ed = utils.spec.expand_to_directional_spectrum(E, freq, dirs, dirp=ds.mwd.values)
    obj = Spectra.from_ds(ds, freq=freq, dirs=dirs, time=ds.valid_time.values)
    obj.set_spec(Ed)
    obj.meta.append({"source": url})
    return obj.ds()
