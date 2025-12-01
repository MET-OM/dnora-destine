from dnora.modelrun.modelrun import ModelRun
from dnora.type_manager.dnora_types import DnoraDataType
import dnora_destine.spectra, dnora_destine.wind, dnora_destine.ice, dnora_destine.waveseries, dnora_destine.ocean, dnora_destine.atmosphere


class ECMWF(ModelRun):
    _reader_dict = {
        DnoraDataType.SPECTRA: dnora_destine.spectra.ECMWF(),
        DnoraDataType.WAVESERIES: dnora_destine.waveseries.ECMWF(),
        DnoraDataType.WIND: dnora_destine.wind.ECMWF(),
        DnoraDataType.ICE: dnora_destine.ice.ECMWF(),
        DnoraDataType.OCEAN: dnora_destine.ocean.ECMWF(),
        DnoraDataType.ATMOSPHERE: dnora_destine.atmosphere.ECMWF(),
    }
