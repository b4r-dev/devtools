"""Convert XFFTS binary file to netCDF.

Usage: $ python xffts2netcdf.py <xffts binary file> <netcdf>

"""

# standard library
import os
import re
import sys
from collections import deque, OrderedDict
from pathlib import Path
from struct import Struct


# dependent packages
import numpy as np
from netCDF4 import Dataset
from tqdm import tqdm


# module constants
CONFIG = (
    ('date', '28s'),
    ('junk1', '4s'),
    ('obsnum', 'q'),
    ('bufpos', '8s'),
    ('scanmode', '8s'),
    ('chopperpos', '8s'),
    ('scancount', 'q'),
    ('speccount', 'q'),
    ('integtime', 'l'),
    ('junk2', '172s'),
    ('array', 'f', 32768)
)


# functions and classes
class Struct2NetCDF:
    def __init__(self, path, config, overwrite=False,
                 byteorder='<', unlimited_dim='t'):
        """Initialize structure-to-netCDF converter.

        Args:
            path (str or path object): Path of netCDF to be created.
            config (tuple of items): Tuple that contains tuple items
                (name, format character, shape) for member in a structure.
            overwrite (bool, optional): If True, the converter overwrites
                an existing netCDF of the same name. Default is False.
            byteorder (str, optional): Format character that indicates
                the byte order of a binary file. Default is for little
                endian ('<'). Use '>' for big endian instead.

        """
        # instance variables
        self.path = Path(path).expanduser()
        self.byteorder = byteorder
        self.unlimited_dim = unlimited_dim

        # check netCDF existance
        if self.path.exists() and not overwrite:
            raise FileExistsError(f'{self.path} already exists')

        # initialization
        self.config = self.parse_config(config)
        self.struct = self.create_struct()
        self.dataset = self.create_empty_dataset()

        # initialize writing counter
        self.n_write = 0

        # aliases
        self.close = self.dataset.close
        self.readsize = self.struct.size

    def write(self, binary):
        """Convert binary data compatible to netCDF format and write it."""
        if len(binary) == 0:
            raise EOFError('Reached the end of file')

        assert len(binary) == self.readsize
        data = deque(self.struct.unpack(binary))

        for name, (fmt, shape) in self.config.items():
            variable = self.dataset[name]

            # in the case of no additional dimensions
            if shape == (1,):
                variable[self.n_write] = data.popleft()
                continue

            # otherwise
            flat = [data.popleft() for i in range(np.prod(shape))]
            variable[self.n_write] = np.reshape(flat, shape)

        self.n_write += 1

    def create_struct(self):
        """Create structure object for unpacking binary string."""
        joined = ''.join(c*np.prod(s) for c, s in self.config.values())
        return Struct(self.byteorder + joined)

    def create_empty_dataset(self):
        """Create empty netCDF dataset according to structure config."""
        # add unlimited dimension
        empty = Dataset(self.path, 'w')
        empty.createDimension(self.unlimited_dim)

        # add variables and additional dimensions
        for name, (fmt, shape) in self.config.items():
            dtype = self.convert_fmt_to_dtype(fmt)

            # in the case of no additional dimensions
            if shape == (1,):
                dims = (self.unlimited_dim,)
                empty.createVariable(name, dtype, dims)
                continue

            # otherwise
            n_dims = len(shape)
            dims = [f'{name}_dim{i}' for i in range(n_dims)]

            for i in range(n_dims):
                dim, size = dims[i], shape[i]
                empty.createDimension(dim, size)

            dims = (self.unlimited_dim,) + tuple(dims)
            empty.createVariable(name, dtype, dims)

        return empty

    @staticmethod
    def parse_config(config):
        """Parse structure config to ordered dictionary."""
        parsed = OrderedDict()

        for item in config:
            if not 2 <= len(item) <= 3:
                raise ValueError(item)

            name, fmt = item[:2]
            shape = (item[2:] or (1,))[0]
            if isinstance(shape, int):
                shape = (shape,)

            assert isinstance(name, str)
            assert isinstance(fmt, str)
            assert isinstance(shape, tuple)

            parsed[name] = fmt, shape

        return parsed

    @staticmethod
    def convert_fmt_to_dtype(fmt):
        """Convert format character to NumPy dtype object."""
        if re.search('[bhil]', fmt, re.I):
            return np.int32
        elif re.search('[q]', fmt, re.I):
            return np.int64
        elif re.search('[ef]', fmt):
            return np.float32
        elif re.search('[d]', fmt):
            return np.float64
        elif re.search('[csp]', fmt):
            return np.str
        elif re.search('[?]', fmt):
            return np.bool
        else:
            raise ValueError(fmt)

    def __enter__(self):
        """Special method for with statement."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Special method for with statement."""
        self.close()


def main():
    """Main function for command line tool."""
    args = sys.argv[1:]

    if not len(args) == 2:
        print(__doc__)
        sys.exit(0)

    xffts  = Path(args[0]).expanduser()
    netcdf = Path(args[1]).expanduser()

    with xffts.open('rb') as f, Struct2NetCDF(netcdf, CONFIG) as g:
        filesize = xffts.stat().st_size
        readsize = g.readsize

        assert not filesize % readsize
        n_struct = int(filesize / readsize)

        for i in tqdm(range(n_struct)):
            binary = f.read(readsize)
            g.write(binary)


# command line tool
if __name__ == '__main__':
    main()