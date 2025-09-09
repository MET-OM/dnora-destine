from dnora.type_manager.data_sources import DataSource
from dnora.type_manager.dnora_types import DnoraDataType
import xarray as xr
from dnora import msg
from dnora_destine.polytope_functions import setup_temp_dir
from dnora.cacher.caching_strategies import CachingStrategy
from dnora.type_manager.spectral_conventions import SpectralConvention
from dnora.read.product_readers import SpectralProductReader
from dnora.read.product_configuration import ProductConfiguration
from dnora.read.file_structure import FileStructure

from dnora.process.spectra import RemoveEmpty
import glob
from functools import partial


from dnora_destine.polytope_functions import (
    download_ecmwf_wave_from_destine,
    ds_wave_polytope_read,
)


class ECMWF(SpectralProductReader):
    product_configuration = ProductConfiguration(
        ds_creator_function=partial(
            ds_wave_polytope_read, freq0=0.04118, nfreq=32, finc=1.1, ndirs=36
        ),
        convention=SpectralConvention.MET,
        default_data_source=DataSource.REMOTE,
        default_folders={
            DataSource.REMOTE: "polytope.lumi.apps.dte.destination-earth.eu",
        },
        filename="",
    )

    file_structure = FileStructure(
        stride=24,
        hours_per_file=24,
    )

    def post_processing(self):
        return RemoveEmpty()

    def caching_strategy(self) -> CachingStrategy:
        return CachingStrategy.SinglePatch

    def get_coordinates(
        self, grid, start_time, source: DataSource, folder: str, **kwargs
    ) -> dict:
        """We only want to do a minimal download to get the coordinates"""
        folder = setup_temp_dir(
            DnoraDataType.SPECTRA, self.name(), clean_old_files=False
        )
        grib_file = f"{folder}/coordinates_ECMWF_destine.grib"

        if glob.glob(grib_file):
            msg.from_file(grib_file)
        else:
            download_ecmwf_wave_from_destine(
                start_time,
                grib_file,
                self.product_configuration.default_folders.get(DataSource.REMOTE),
            )
        ds = xr.open_dataset(grib_file, engine="cfgrib", decode_timedelta=True)
        return {"lat": ds.latitude.values, "lon": ds.longitude.values}
