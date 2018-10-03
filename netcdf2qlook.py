#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import re
from pathlib import Path

import numpy as np
import xarray as xr
from bokeh.io import output_file, save
from bokeh.layouts import gridplot
from bokeh.plotting import figure


SCIS_DIR = Path("../scis").expanduser()
CALS_DIR = Path("../cals").expanduser()
QLOOK_DIR = Path("../qlooks").expanduser()
IF_LABEL_DICT = {
    1: "B-Pol LSB (IF 1)",
    2: "B-Pol USB (IF 2)",
    3: "A-Pol LSB (IF 3)",
    4: "A-Pol USB (IF 4)",
}


class NetCDF2Qlook(object):
    """
    """
    def __init__(self, sci_id, cal_id, title="Q-Look Plot"):
        self.scis = [SCIS_DIR / f"xffts{sci_id}.xfftsx.0{i}.nc"
                    for i in range(1, 5)]
        if not all([sci.exists for sci in self.scis]):
            return AssertionError

        self.cals = [CALS_DIR / f"xffts{cal_id}.xfftsx.0{i}.nc"
                     for i in range(1, 5)]
        if not all([cal.exists for cal in self.cals]):
            return AssertionError

        self.sci_id = sci_id
        self.cal_id = cal_id
        self.title = title

    def map(self):
        """
        """
        pass

    def psw(self):
        """
        """
        Tamb = 273.
        freq = (128 - 0.1) + np.linspace(0., 2.5, 2**15)

        Rs = []
        ONs = []
        OFFs = []
        for s, c in zip(self.scis, self.cals):
            with xr.open_dataset(s) as sci, \
                    xr.open_dataset(c) as cal:
                Rs.append((cal["array"]/cal["integtime"]).mean("t"))
                ONs.append((sci["array"]/sci["integtime"])[sci["bufpos"]=="ON"])
                OFFs.append((sci["array"]/sci["integtime"])[sci["bufpos"]=="REF"])
        Tcals = [Tamb * (on - off[1:]) / (r - off[1:])
                 for r, on, off in zip(Rs, ONs, OFFs)]
        # Tcals = [t - t.mean("array_dim0") for t in Tcals]

        plots = []
        colors = ["tomato", "olivedrab", "palevioletred", "steelblue"]
        for i, (t, c) in enumerate(zip(Tcals, colors)):
            if i == 0:
                p = figure(title=self.title, plot_width=640, plot_height=360)
            else:
                p = figure(plot_width=640, plot_height=360)
            p.line(freq, t.mean("t").values,
                   color=c, line_width=1., legend=IF_LABEL_DICT[i+1])

            p.title.text_font_size = "16pt"
            p.legend.location = "top_right"
            p.legend.background_fill_alpha = 0.5
            p.xaxis.axis_label = "Frequency [GHz]"
            p.xaxis.axis_label_text_font_size = "12pt"
            p.xaxis.axis_label_text_font_style = "bold"
            p.yaxis.axis_label = "Power [K]"
            p.yaxis.axis_label_text_font_size = "12pt"
            p.yaxis.axis_label_text_font_style = "bold"

            plots.append(p)

        plots = gridplot([plots[0], plots[1]], [plots[2], plots[3]])
        return plots


    def timestream(self):
        """
        """
        with xr.open_dataset(self.scis[0]) as data:
            _arrays = data["array"]
            _integ_data = np.average(_arrays, axis=1)
            _x = np.arange(len(_integ_data))

        p = figure(title=self.title, plot_width=960, plot_height=540)
        p.line(_x, _integ_data, line_color="midnightblue", line_width=1.)
        p.title.text_font_size = "16pt"
        p.xaxis.axis_label = "Time stream"
        p.xaxis.axis_label_text_font_size = "12pt"
        p.xaxis.axis_label_text_font_style = "bold"
        p.yaxis.axis_label = "Power [a.u.]"
        p.yaxis.axis_label_text_font_size = "12pt"
        p.yaxis.axis_label_text_font_style = "bold"

        return p
    

    def save(self, plot):
        """
        """
        _qlook = QLOOK_DIR / f"{self.sci_id}.html"
        output_file(_qlook)
        save(plot)


def main():
    """
    """
    parser = argparse.ArgumentParser(
        prog="netcdf2qlook",
        usage="Create Q-look plot ('Bokeh' html file)",
        description="description",
        add_help=True,
    )
    parser.add_argument("sci_id", help="date of the data")
    parser.add_argument("cal_id", help="date of the calibration data")
    parser.add_argument("plot", type=str, choices=["map", "psw", "timestream"],
                        help="a kind of plot")
    parser.add_argument("-t", "--title", type=str, dest="title", help="title of plot") 
    args = parser.parse_args()

    if args.title is not False:
        n2q = NetCDF2Qlook(args.sci_id, args.cal_id, args.title)
    else:
        n2q = NetCDF2Qlook(args.sci_id, args.cal_id)

    if args.plot == "map":
        plot = n2q.map()
    elif args.plot == "psw":
        plot = n2q.psw()
    elif args.plot == "timestream":
        plot = n2q.timestream()
    else:
        raise AssertionError
    n2q.save(plot)

    return


if __name__ == "__main__":
    main()
