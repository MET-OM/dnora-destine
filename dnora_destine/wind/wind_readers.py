from dnora.type_manager.data_sources import DataSource

from dnora.read.product_readers import ProductReader
from dnora.read.product_configuration import ProductConfiguration
from dnora.read.file_structure import FileStructure

from dnora_destine.polytope_functions import ds_polytope_read


class ECMWF(ProductReader):
    """Downloads ECMWF data from Desinte using polytope api"""

    product_configuration = ProductConfiguration(
        ds_creator_function=ds_polytope_read,
        default_data_source=DataSource.REMOTE,
    )

    file_structure = FileStructure(stride=24, hours_per_file=24)
