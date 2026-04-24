#!/usr/bin/env python3

import sys
argv = sys.argv
sys.argv = argv[:1]

import argparse

import os

import ROOT


#
# default parser
#

def defaultParser():
    sys.argv = argv

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--pycfg",
        dest="pycfg",
        help="input configuration file",
        default="configuration.py",
    )

    return parser


#
# load configurations into the parser, according to configuration.py
#

def loadDefaultOptions(parser, pycfg=None, quiet=False):

    if pycfg != None and os.path.exists(pycfg):
        # print ("loadDefaultOptions: pycfg = ", pycfg)
        handle = open(pycfg,'r')
        local_variables = {}
        exec(handle.read(),local_variables)
        handle.close()
        # clean the dictionary to remove globals due to "exec" funcionality
        local_variables = {k: v for k, v in local_variables.items() if not (k.startswith('__') and k.endswith('__'))}
        for opt_name, opt_value in local_variables.items():
          parser.add_argument('--' + opt_name, default=opt_value)
        return
    else:
        return








if __name__ == '__main__':
    sys.argv = argv

    header = """
         --------------------------------------------------------------------------------------------------
         '                                                                                                '
         '      ___|                              |             |         \  |         |                  '
         '    \___ \   __ \    _` |  __ \    __|  __ \    _ \   __|      |\/ |   _` |  |  /   _ \   __|   '
         '          |  |   |  (   |  |   | \__ \  | | |  (   |  |        |   |  (   |    <    __/  |      '
         '    _____/  _|  _| \__,_|  .__/  ____/ _| |_| \___/  \__|     _|  _| \__,_| _|\_\ \___| _|      '
         '                          _|                                                                    '
         '                                                                                                '
         --------------------------------------------------------------------------------------------------
         """

    print(header)

    parser = defaultParser()

    parser.add_argument("--submitBatch", action='store_true', dest="submitBatch",   help="Trigger the submission to lxbatch")


    opt = parser.parse_args()
    print ("opt.pycfg            = ", opt.pycfg)
    loadDefaultOptions(parser, opt.pycfg)
    opt = parser.parse_args()



    variables_to_dump = []


    #
    # logic of dependencies:
    #
    #    samples.py
    #      --> aliases.py     since the aliases/defines will be "Defined" only for selected samples
    #    cuts.py
    #    variables.py
    #    snapshot.py
    #


    #
    # read list of samples
    #
    samples = {}
    if os.path.exists(opt.samplesFile) :
      handle = open(opt.samplesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      samples = {k: v for k, v in samples.items() if not (k.startswith('__') and k.endswith('__'))}

    # print ("samples = ", samples)

    #
    # read list of variables
    #
    variables = {}
    if os.path.exists(opt.variablesFile) :
      handle = open(opt.variablesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      variables = {k: v for k, v in variables.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("variables = ", variables)


    #
    # read list of cuts
    #
    cuts = {}
    supercut = ''
    if os.path.exists(opt.cutsFile) :
      handle = open(opt.cutsFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      cuts = {k: v for k, v in cuts.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("cuts = ", cuts)
    print ("supercut = ", supercut)





    #
    # read configuration for the snapshot
    #
    variables_to_dump = []
    cut_to_dump = ''
    folder_where_to_save_trees = ''

    if os.path.exists(opt.snapshotFile) :
      handle = open(opt.snapshotFile,'r')
      exec(handle.read())
      handle.close()

    print ("variables_to_dump = ", variables_to_dump)
    print ("cut_to_dump = ", cut_to_dump)
    print ("folder_where_to_save_trees = ", folder_where_to_save_trees)



