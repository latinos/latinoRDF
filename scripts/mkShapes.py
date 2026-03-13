#!/usr/bin/env python3

import sys
argv = sys.argv
sys.argv = argv[:1]

import argparse

import os


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
         '                ___|   |                               \  |         |                           '
         '              \___ \   __ \    _` |  __ \    _ \      |\/ |   _` |  |  /   _ \   __|            '
         '                    |  | | |  (   |  |   |   __/      |   |  (   |    <    __/  |               '
         '              _____/  _| |_| \__,_|  .__/  \___|     _|  _| \__,_| _|\_\ \___| _|               '
         '                                    _|                                                          '
         '                                                                                                '
         --------------------------------------------------------------------------------------------------
         """

    print(header)

    parser = defaultParser()
    opt = parser.parse_args()
    print ("opt.pycfg            = ", opt.pycfg)
    loadDefaultOptions(parser, opt.pycfg)
    opt = parser.parse_args()

    print ("opt.tag              = ", opt.tag)
    print ("opt.variablesFile    = ", opt.variablesFile)
    print ("opt.cutsFile         = ", opt.cutsFile)
    print ("opt.samplesFile      = ", opt.samplesFile)
    print ("opt.nuisancesFile    = ", opt.nuisancesFile)
    print ("opt.lumi             = ", opt.lumi)
    print ("opt.outputDir        = ", opt.outputDir)

    # not used by mkShapes
    # print ("opt.structureFile    = ", opt.structureFile)

    #
    # logic of dependencies:
    #
    #    samples.py
    #      --> nuisances.py   since some nuisances are defined only for some samples
    #    cuts.py
    #      --> nuisances.py   since some nuisances are defined only for some cuts (e.g. lnN of migration)
    #    nuisances.py
    #    variables.py
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

    print ("samples = ", samples)

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
    if os.path.exists(opt.cutsFile) :
      handle = open(opt.cutsFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      cuts = {k: v for k, v in cuts.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("cuts = ", cuts)


    #
    # read list of nuisances
    #
    nuisances = {}
    if os.path.exists(opt.nuisancesFile) :
      handle = open(opt.nuisancesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      nuisances = {k: v for k, v in nuisances.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("nuisances = ", nuisances)







    print ("\n\n")
    print (" I'm done ... \n\n")













