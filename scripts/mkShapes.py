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



# ----------------------------------------------------- ShapeFactory --------------------------------------

import logging
import subprocess


class ShapeFactory:
    _logger = logging.getLogger('ShapeFactory')

    # _____________________________________________________________________________
    def __init__(self):

        variables = {}   # FIXME needed?
        self._variables = variables

        cuts = {}
        self._cuts = cuts

        samples = {}
        self._samples = samples

        aliases = {}
        self._aliases = aliases

        self._lumi = 1

        self._treeName = 'latino'

        self._outputDir = './test/'

        self._outputRootFile = 'myhistos.root'

        self._script_batch_location = './scripts_batch/'

        self._scripts_run_folder = "scripts_run"

        # conditions
        self._silentMode = False



    # _____________________________________________________________________________
    def __del__(self):
        pass


    # _____________________________________________________________________________
    #                                                              "file_path" is a list of root files!
    def create_cpp_source_list_of_files(self, output_name, tree_name, file_path, output_root_file_name, sampleName, weight, aliases_to_be_defined):
        # This is your C++ template as a Python string

        define_input_files_logic = ""

        define_input_files_logic += f"//  Nominal input files\n"

        define_input_files_logic += f'    auto* nominal = new TChain("{tree_name}");\n'

        # define_input_files_logic += f'    nominal->Add("{file_path}");\n'

        for file_name in file_path:
          define_input_files_logic += f'    nominal->Add("{file_name}");\n'

        #
        # now define the nuisances based on alternative trees
        #
        # 'kind': 'suffix',
        # 'type': 'shape',
        #
        # 'mapUp': 'ElepTup',
        # 'mapDown': 'ElepTdo',
        #
        #      'folderUp'    :   '/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer20UL18_106x_nAODv9_Full2018v9/MCl1loose2018v9__MCCorr2018v9NoJERInHorn__l2tightOR2018v9__ElepTup_suffix'
        #      'folderDown'   : ...
        #
        #

        #
        # extract name of root file nominal, without folder path
        #


        define_input_files_logic += f"//  Variations input files (if any)\n"

        for nuisanceName, nuisance in self._nuisances.items():

          if sampleName in nuisance['samples'].keys() and nuisance['type'] == 'shape' and ('kind' in nuisance.keys() and nuisance['kind'] == 'suffix'):

            # One TChain up and one TChain down, then add all the root files
            define_input_files_logic += f'''    auto* friend_{nuisance['mapUp']} = new TChain("{tree_name}");\n'''
            define_input_files_logic += f'''    auto* friend_{nuisance['mapDown']} = new TChain("{tree_name}");\n'''

            for file_name in file_path:

              # Find the index of the first "/" from the right
              index = file_name.rfind("/")
              # Extract everything from that index + 1 to the end
              # (We add 1 so we don't include the "/" itself)
              file_path_only_file_no_folder = file_name[index + 1:]

              define_input_files_logic += f'''    friend_{nuisance['mapUp']}->Add("{nuisance['folderUp']}/{file_path_only_file_no_folder}");\n'''
              define_input_files_logic += f'''    friend_{nuisance['mapDown']}->Add("{nuisance['folderDown']}/{file_path_only_file_no_folder}");\n'''

            # add friend TChain only once
            define_input_files_logic += f'''    nominal->AddFriend(friend_{nuisance['mapUp']}, "{nuisance['mapUp']}");\n'''
            define_input_files_logic += f'''    nominal->AddFriend(friend_{nuisance['mapDown']}, "{nuisance['mapDown']}");\n'''

            # varied branches are the same for all "added" trees
            define_input_files_logic += f'''    auto varBranches_{nuisance['mapUp']} = getBranchNames(friend_{nuisance['mapUp']});\n'''
            define_input_files_logic += f'''    auto varBranches_{nuisance['mapDown']} = getBranchNames(friend_{nuisance['mapDown']});\n'''


        define_input_files_logic += f'    ROOT::RDataFrame base_df(*nominal);\n'
        # define_input_files_logic += f'    ROOT::RDF::RInterface varied_df = base_df;\n'
        define_input_files_logic += f'    auto varied_df = ROOT::RDF::RNode(base_df);\n'


        #
        # define the weights needed for this specific sample
        #
        define_weights = ""
        define_weights += f"//  weigths needed\n"
        define_weights += f'    varied_df = SafeDefine(varied_df, "my_sample_weight", "{weight}");\n'

        #
        # define the aliases needed for this specific sample
        #
        define_aliases = ""
        define_aliases += f"//  aliases/define needed\n"

        for aliasName, alias in aliases_to_be_defined.items():
          define_aliases += f'    varied_df = SafeDefine(varied_df, "{aliasName}", "{alias}");\n'



        #
        # register the variations
        #

        register_variations_logic = ""

        register_variations_logic += f"//  Register the variations\n"

        if len(self._nuisances) != 0 :
          first_time_suffix = 0
          for nuisanceName, nuisance in self._nuisances.items():

            #
            # "shape" : "suffix" nuisances
            #  a.k.a. alternative friend trees
            #  also the use of a different weight is possible, to be activated with "weigthsPerSample"    FIXME  Not yet implemented ... was this ever used?
            #
            #  e.g.
            #    'mapUp': 'ElepTup',
            #    'mapDown': 'ElepTdo',
            #    'samples': dict((skey, ['1', '1']) for skey in mcALL),
            #    'folderUp': makeMCDirectory('ElepTup_suffix'),
            #    'folderDown': makeMCDirectory('ElepTdo_suffix'),
            #    'weigthsPerSample': true
            #
            #
            if sampleName in nuisance['samples'].keys() and nuisance['type'] == 'shape' and ('kind' in nuisance.keys() and nuisance['kind'] == 'suffix'):

              if first_time_suffix == 0 :
                register_variations_logic += f'    int suffix_size = 0;\n'
                first_time_suffix = 1

              register_variations_logic += f'''    suffix_size = {len(nuisance['mapUp']) + 1};\n'''
              register_variations_logic += f'''    for (const auto& branch : varBranches_{nuisance['mapUp']}) {{\n'''
              # register_variations_logic += f'''      if (branch.ends_with("{nuisance['mapUp']}")) {{\n'''
              register_variations_logic += f'''      if (int(branch.size()) >= (suffix_size-1) && branch.compare(branch.size() - (suffix_size-1), (suffix_size-1), "{nuisance['mapUp']}") == 0 ) {{\n'''
              register_variations_logic += f'''        std::string nomCol = branch.substr(0, branch.size() - suffix_size);\n'''
              register_variations_logic += f'''        std::string expression = "ROOT::RVec<" + varied_df.GetColumnType(nomCol) + ">{{" + branch + "}}";\n'''
              register_variations_logic += f'''        varied_df = varied_df.Vary(\n'''
              register_variations_logic += f'''                                  nomCol,\n'''
              register_variations_logic += f'''                                  expression,\n'''
              register_variations_logic += f'''                                  {{"up"}},\n'''
              # register_variations_logic += f'''                                  "{nuisance['mapUp']}"\n'''
              register_variations_logic += f'''                                  "{nuisance['name']}"\n'''
              register_variations_logic += f'''                                  );\n'''
              register_variations_logic += f'''      }};\n'''
              register_variations_logic += f'''    }};\n'''

              register_variations_logic += f'''    \n'''
              register_variations_logic += f'''    suffix_size = {len(nuisance['mapDown']) + 1};\n'''
              register_variations_logic += f'''    for (const auto& branch : varBranches_{nuisance['mapDown']}) {{\n'''
              # register_variations_logic += f'''      if (branch.ends_with("{nuisance['mapDown']}")) {{\n'''
              register_variations_logic += f'''      if (int(branch.size()) >= (suffix_size-1) && branch.compare(branch.size() - (suffix_size-1), (suffix_size-1), "{nuisance['mapDown']}") == 0 ) {{\n'''
              register_variations_logic += f'''        std::string nomCol = branch.substr(0, branch.size() - suffix_size);\n'''
              register_variations_logic += f'''        std::string expression = "ROOT::RVec<" + varied_df.GetColumnType(nomCol) + ">{{" + branch + "}}";\n'''
              register_variations_logic += f'''        varied_df = varied_df.Vary(\n'''
              register_variations_logic += f'''                                  nomCol,\n'''
              register_variations_logic += f'''                                  expression,\n'''
              register_variations_logic += f'''                                  {{"do"}},\n'''
              # register_variations_logic += f'''                                  "{nuisance['mapDown']}"\n'''
              register_variations_logic += f'''                                  "{nuisance['name']}"\n'''
              register_variations_logic += f'''                                  );\n'''
              register_variations_logic += f'''      }};\n'''
              register_variations_logic += f'''    }};\n'''

            #
            # "shape" : "weight" nuisances
            #  a.k.a. same tree but with a different weight
            #
            #  e.g. nominal,         up,             down
            #    ['SFweightMu','SFweightMuUp', 'SFweightMuDown']
            #
            #
            if sampleName in nuisance['samples'].keys() and nuisance['type'] == 'shape' and ('kind' in nuisance.keys() and nuisance['kind'] == 'weight'):

              #
              # check if '{nuisance['samples'][sampleName][0]}' is in the string 'weight' (that is actually defined in 'my_sample_weight')
              # if yes, propagate the weight variation

              if nuisance['samples'][sampleName][0] in weight:

                variation_up   =  weight.replace(nuisance['samples'][sampleName][0], nuisance['samples'][sampleName][1])
                variation_down =  weight.replace(nuisance['samples'][sampleName][0], nuisance['samples'][sampleName][2])

                register_variations_logic += f'''    varied_df = varied_df.Vary(\n'''
                register_variations_logic += f'''      "my_sample_weight",\n'''
                register_variations_logic += f'''      "ROOT::RVecD{{{variation_up},{variation_down}}}",\n'''
                register_variations_logic += f'''      {{"up", "do"}},\n'''
                register_variations_logic += f'''      "{nuisance['name']}"\n'''
                register_variations_logic += f'''      );\n'''



              # register_variations_logic += f'''    std::string expression_{nuisanceName} = "ROOT::RVecD{{{nuisance['samples'][sampleName][1]},{nuisance['samples'][sampleName][2]}}}";\n'''
              # register_variations_logic += f'''    varied_df = varied_df.Vary(\n'''
              # register_variations_logic += f'''                              "{nuisance['samples'][sampleName][0]}",\n'''
              # register_variations_logic += f'''                              expression_{nuisanceName},\n'''
              # register_variations_logic += f'''                              {{"up", "down"}}\n'''
              # register_variations_logic += f'''                              );\n'''
              #
              #
        booking_logic = ""

        #
        # In RDataFrame, all variables must be defined before being plotted
        # The pro of this is that they can be used also in cuts
        #
        #
        # In case of already defined variables, for example "mll", and "mll" is already defined in the TTree,
        # the code "SafeDefine" should handle this, and "Define" a variable only when needed
        #

        booking_logic += f"//  Initial ...\n"
        booking_logic += f'    auto current_node = ROOT::RDF::RNode(varied_df);\n'


        define_variables_logic = ""
        define_variables_logic += f"//  I need to define the RNode, otherwise SafeDefine will not work\n"
        define_variables_logic += f"    // Define variables \n"
        for variableName, variable in self._variables.items():
            name = variable['name']
            define_variables_logic += f'    current_node = SafeDefine(current_node, "{variableName}", "{name}");\n'

        #
        # once all variables are defined, they can be used and plotted with "variableName"
        #
        # In root file:    <cut>/<variable>/histo_<sample>
        #
        for cutName, cut in self._cuts.items():
          #
          # cuts could be nested, i.e. cut -> categories
          # here is where you exploit the full power of RDataFrame
          #
          # Procedure:
          # - check if categories
          # - if yes, then define the cuts in a nested way
          # - otherwise if "expr" is defined use it
          #   if note use directly "cut"
          #
          # Different possibilities:
          #
          # cut["DY"] = "mll>50 && mll<120"
          # cut["DY"] = {   'expr': 'mll>70 && mll<110' }
          # cut["DY"] = {
          #    'expr': 'mll>70 && mll<110',
          #    'categories' : {
          #       'eleele' : 'ee',   # "ee" is defined in aliases.py
          #       'mumu'   : 'mm',   # "mm" is defined in aliases.py
          #      }
          #    }
          #

          list_cuts = {}
          if isinstance(cut, dict):
            # "cut" is a dictionary
            expression = cut['expr']
            categories = cut.get('categories', {})
            if categories :
              list_cuts[ cutName ] = "(" + expression + ")"   # add the un-categorized phase space too! it comes "for free"
              for category_name, category in categories.items():
                list_cuts[ cutName + "_" + category_name] = "(" + expression + ") && (" + category + ")"
            else :
              list_cuts[ cutName ] = expression
          else :
            list_cuts[ cutName ] = cut


          mother_cut_name = ""
          for icut, (this_cutName, this_cut) in enumerate(list_cuts.items()):
            if len(list_cuts) > 1 :
              if icut == 0:
                define_variables_logic += f'    auto node_{this_cutName} = current_node.Filter("{this_cut}", "{this_cutName}");\n'
                mother_cut_name = this_cutName
              else:
                # with this I'm nesting the node into the "mother node" -> it's RDataFrame power
                define_variables_logic += f'    auto node_{this_cutName} = node_{mother_cut_name}.Filter("{this_cut}", "{this_cutName}");\n'
            else :
              define_variables_logic += f'    auto node_{this_cutName} = current_node.Filter("{this_cut}", "{this_cutName}");\n'

            for variableName, variable in self._variables.items():
                (bins, v_min, v_max) = variable['range']
                # FIXME: folding needed

                # We add each RResultPtr to a vector called 'histograms'
                define_variables_logic += f'    hist_map["{this_cutName}"].push_back(node_{this_cutName}.Histo1D({{"h_{variableName}", "{variableName}", {bins}, {v_min}, {v_max}}}, "{variableName}", "my_sample_weight"));\n'


        define_variables_logic += f'    \n'
        define_variables_logic += f'    std::vector<std::string> list_of_variables;\n'
        for variableName, variable in self._variables.items():
          define_variables_logic += f'    list_of_variables.push_back("{variableName}");\n'




        cpp_code = f"""
#include "ROOT/RDataFrame.hxx"
#include "ROOT/RDFHelpers.hxx"
#include "ROOT/RVec.hxx"

#include "TFile.h"
#include "TH1D.h"
#include "TDirectory.h"
#include "TChain.h"
#include <map>
#include <vector>
#include <iostream>
#include <string>
#include <typeinfo>



ROOT::RDF::RNode SafeDefine(ROOT::RDF::RNode df, std::string name, std::string expr) {{
    auto colNames = df.GetColumnNames();
    if (std::find(colNames.begin(), colNames.end(), name) == colNames.end()) {{
        return df.Define(name, expr);
    }}
    return df;
}}


std::vector<std::string> getBranchNames(TTree* tree) {{
  std::vector<std::string> names;
  TObjArray* branches = tree->GetListOfBranches();
  for (int i = 0; i < branches->GetEntries(); ++i)
    names.push_back(branches->At(i)->GetName());
  return names;
}}



int main() {{
    ROOT::EnableImplicitMT();

    // --- Automatically generated input root files ---

    {define_input_files_logic}

    // ----------------------------------------

    std::map<std::string, std::vector<ROOT::RDF::RResultPtr<TH1D>>> hist_map;

    // --- Automatically generated define aliases ---

    {define_aliases}

    // ----------------------------------------

    // --- Automatically generated define weights ---

    {define_weights}

    // ----------------------------------------


    // --- Automatically generated register nuisances variations ---

    {register_variations_logic}

    // ----------------------------------------

    // --- Automatically generated ... just the main node ---

    {booking_logic}

    //
    // from now on: current_node
    // ----------------------------------------

    // --- Automatically generated define cuts and histograms ---

    {define_variables_logic}

    // ----------------------------------------


    //
    // In root file:    <cut>/<variable>/histo_<sample>
    //

    TFile out_file("{self._outputDir}/{output_root_file_name}", "RECREATE");
    for (auto& [cut_label, h_list] : hist_map) {{
        // Create a folder for this cut
        TDirectory *dir = out_file.mkdir(cut_label.c_str());
        int ivar = 0;
        for (auto& h : h_list) {{
            dir->cd();
            TDirectory *subdir = out_file.mkdir( (cut_label+"/"+list_of_variables.at(ivar)).c_str() );
            subdir->cd();
            ivar++;

            // get the nominal and the variations too
            auto all_histos = ROOT::RDF::Experimental::VariationsFor(h);

            for (auto& [name, histo] : all_histos) {{
              std::string temp_name;
              if (name == "nominal") {{
                  temp_name = "histo_{sampleName}";
              }}
              else {{
                temp_name = name.c_str();
                // scale_e_2018_UL:up --> scale_e_2018_ULup
                temp_name.erase(std::remove(temp_name.begin(), temp_name.end(), ':'), temp_name.end());
                //size_t pos = temp_name.find(':');
                //if (pos != std::string::npos) {{
                //  temp_name = temp_name.substr(0, pos);
                //}}
                temp_name = ("histo_{sampleName}_" + temp_name);
              }}
              gDirectory = subdir;
              histo->SetName(temp_name.c_str());
              histo->Write();
            }}
        }}
        out_file.cd(); // Go back to root for the next directory
    }}
    out_file.Close();

    return 0;
}}

        """


        with open(f"{output_name}.cpp", "w") as f:
            f.write(cpp_code)
        # print(f"Created {output_name}.cpp")


    # _____________________________________________________________________________
    def compile_cpp(self, source_name):
        # Get ROOT flags automatically using 'root-config'
        root_flags = subprocess.check_output(["root-config", "--cflags", "--libs"]).decode().strip()

        # Construct the compilation command
        compile_cmd = f"g++ -O2 {source_name}.cpp -o {source_name} {root_flags}"
        # compile_cmd = f"g++ -O3 {source_name}.cpp -o {source_name} {root_flags}"

        print(f"Compiling...")
        result = os.system(compile_cmd)

        if result == 0:
            print(f"Compilation successful: ./{source_name}")
        else:
            print("Compilation failed!")


    # _____________________________________________________________________________
    def generate_makefile(self, file_paths, makefile_name="Makefile"):
        # Get ROOT configuration via shell calls
        cpp_flags = "$(shell root-config --cflags)"
        ld_flags = "$(shell root-config --libs)"
        type_of_compilation = "-O2"
        # from "blabla.cpp" to "blabla"
        targets = [os.path.splitext(f)[0] for f in file_paths]

        with open(makefile_name, "w") as f:
            f.write("# Generated Makefile\n")
            f.write("CXX = g++\n")
            # f.write(f"CXXFLAGS = {type_of_compilation} -Wall {cpp_flags} -std=c++20 -Wcpp \n")  # c++20 used for "ends_with"
            f.write(f"CXXFLAGS = {type_of_compilation} -Wall {cpp_flags} \n")
            f.write(f"LDFLAGS = {ld_flags}\n\n")

            # 'all' target: the list of all executables to be created
            all_targets = " ".join(targets)
            f.write(f"all: {all_targets}\n\n")

            # The Pattern Rule
            # This says: To create ANY executable 'X', look for 'X.cpp'
            # It works across subdirectories automatically.
            f.write("%: %.cpp\n")
            f.write("\t$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)\n\n")

            # Clean target
            f.write("clean:\n")
            f.write(f"\trm -f {all_targets}\n")


    # _____________________________________________________________________________
    def setValues(self, outputDir, variables, cuts, samples, nuisances, aliases, lumi):

        self._variables = variables
        self._samples   = samples
        self._cuts      = cuts
        self._nuisances = nuisances
        self._aliases   = aliases
        self._outputDir = outputDir
        self._lumi      = lumi

    # _____________________________________________________________________________
    def setConditions(self, silentMode):

        self._silentMode = silentMode


    # _____________________________________________________________________________
    def makeNominals(self):

        print ("======================")
        print ("==== makeNominals ====")
        print ("======================")

        os.system ("mkdir " + self._outputDir + "/")

        ROOT.TH1.SetDefaultSumw2(True)

        os.system ("mkdir " + self._scripts_run_folder + "/")

        list_of_files_to_compile = []

        # print ("length of samples = ", len(self._samples))
        #
        # Loop over samples
        #
        for sampleName, sample in self._samples.items():
          os.system ("mkdir " + self._scripts_run_folder + "/" + sampleName + "/")
          #
          # create an executable for each file in each sample
          #
          # samples is a dictionary: {'subname' : [list of root files] }
          #
          # print ("length of sample['name'] = ", len(sample['name']))


          weight = sample['weight'] if 'weight' in sample.keys() else "1."

          #
          # check if "isData". If NOT isData then multiply by lumi otherwise no
          #
          if 'isData' in sample.keys() :
            if not (len(sample ['isData']) == 1 and sample ['isData'][0] == 'all') :
              # if you put 'all', all the root files are considered "data"
              # ok, it's data ... and so now?
              #
              pass
          else : # default is "scale to luminosity"
            weight = f"({weight}) * {self._lumi}"


          #
          # check if additional "Define" is needed, from "alises"
          #
          aliases_to_be_defined = {}
          for aliasName, alias in self._aliases.items():
            if 'samples' in alias.keys():
              if sampleName in alias['samples']:
                aliases_to_be_defined[aliasName] = alias['expr']


          for subname, list_root_files in sample['name'].items():
            print ("length of list_root_files = ", len(list_root_files))
            os.system ("mkdir " + self._scripts_run_folder + "/" + sampleName + "/" + subname + "/")

            #
            # Merge together different root files in one single job, not to have billions of jobs :)
            #
            make_job_every_N = 1
            if "FilesPerJob" in sample.keys():
              make_job_every_N = sample['FilesPerJob']
            #
            # create a list of lists of root files, one per job to be submitted
            # [ [root1, root2, root3], [root4, root5]]
            #
            chunks_list_root_files = [list_root_files[i:i + make_job_every_N] for i in range(0, len(list_root_files), make_job_every_N)]

            for i, root_files in enumerate(chunks_list_root_files):
              # name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + str(i)
              name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              tree = "Events"

              output_root_file_name = "root_file___" + sampleName + "_" + subname + "_" + str(i) + ".root"

              self.create_cpp_source_list_of_files(name_code, tree, root_files, output_root_file_name, sampleName, weight, aliases_to_be_defined)

              list_of_files_to_compile.append(name_code)
              # self.compile_cpp(name_code)


            # for i, root_file in enumerate(list_root_files):
            #   # name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + str(i)
            #   name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
            #   tree = "Events"
            #
            #   output_root_file_name = "root_file___" + sampleName + "_" + subname + "_" + str(i) + ".root"
            #
            #   self.create_cpp_source_single_file(name_code, tree, root_file, output_root_file_name, sampleName, weight, aliases_to_be_defined)
            #
            #   list_of_files_to_compile.append(name_code)
            #   # self.compile_cpp(name_code)


        self.generate_makefile(list_of_files_to_compile)

        # Run the compilation in parallel
        print("Start parallel compilation...")
        subprocess.run(["make", "-j8"])
        #
        # subprocess.run() is a blocking call -> it will make the compilation to end before the next step
        #

        # Now you can run it:
        # subprocess.run([f"./{name_code}"])


    # _____________________________________________________________________________
    def submitBatch(self):

        print ("======================")
        print ("==== submit Batch ====")
        print ("======================")

        os.system ("mkdir " + self._script_batch_location + "/")

        submission_dir = os.getcwd()

        #
        # Loop over samples
        #
        for sampleName, sample in self._samples.items():
          os.system ("mkdir " + self._script_batch_location + "/" + sampleName + "/")

          for subname, list_root_files in sample['name'].items():
            os.system ("mkdir " + self._script_batch_location + "/" + sampleName + "/" + subname + "/")

            make_job_every_N = 1
            if "FilesPerJob" in sample.keys():
              make_job_every_N = sample['FilesPerJob']
            chunks_list_root_files = [list_root_files[i:i + make_job_every_N] for i in range(0, len(list_root_files), make_job_every_N)]

            for i, root_files in enumerate(chunks_list_root_files):
              name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              name_code_no_folder = "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              name_bash = self._script_batch_location + "/" + sampleName + "/" + subname + "/" + "my_script_" + str(i) + ".sh"
              output_root_file_name = "root_file___" + sampleName + "_" + subname + "_" + str(i) + ".root"

              bash_code = f"""#!/bin/bash
set -e  # Exit on error
echo "Job started at $(date)"
echo "Running on node $(hostname)"
mkdir {self._outputDir}
./{name_code_no_folder}
cp {self._outputDir}/{output_root_file_name}  {submission_dir}/{self._outputDir}/

echo "Current directory content after running:"
ls -lh
echo "Current full path: $(pwd)"

"""

              with open(f"{name_bash}", "w") as f:
                f.write(bash_code)
                os.system ("chmod +x " + name_bash)
                # print ("name_bash = ", name_bash)

              name_submit = submission_dir + "/" + self._script_batch_location + "/" + sampleName + "/" + subname + "/" + "my_script_" + str(i) + ".sub"
              # name_folder = submission_dir + "/" + self._script_batch_location + "/" + sampleName + "/" + subname + "/"
              name_folder = self._script_batch_location + "/" + sampleName + "/" + subname + "/"
              name_folder_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/"
              name_bash_no_folder = "my_script_" + str(i) + ".sh"

              if self._silentMode :
                output_file = "/dev/null"
                error_file  = "/dev/null"
                log_file    = "/dev/null"
              else :
                output_file = f"log/{name_bash_no_folder}.out"
                error_file  = f"log/{name_bash_no_folder}.err"
                log_file    = f"log/{name_bash_no_folder}.log"


              submit_code = f"""
initialdir            = {name_folder}
executable            = {name_bash}
transfer_input_files  = {submission_dir}/{name_folder_code}{name_code_no_folder}
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
output                = {output_file}
error                 = {error_file}
log                   = {log_file}
getenv                = True
+JobFlavour           = "longlunch"
queue
"""

              with open(f"{name_submit}", "w") as f:
                f.write(submit_code)

              print("Submitting job to HTCondor: condor_submit " + name_submit)
              subprocess.run(["condor_submit", f"{name_submit}"])

#
#
#  Main
#
#

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

    parser.add_argument("--submitBatch", action='store_true', dest="submitBatch",   help="Trigger the submission to lxbatch")
    parser.add_argument("--hadd",        action='store_true', dest="haddRootFiles", help="Trigger the merging of the root files")
    parser.add_argument("--silentMode",  action='store_true', dest="silentMode",    help="Remove as much as possible the print and the log/err files production")

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

    print ("opt.submitBatch      = ", opt.submitBatch)
    print ("opt.hadd             = ", opt.haddRootFiles)
    print ("opt.silentMode       = ", opt.silentMode)




    # not used by mkShapes
    # print ("opt.structureFile    = ", opt.structureFile)

    #
    # logic of dependencies:
    #
    #    samples.py
    #      --> nuisances.py   since some nuisances are defined only for some samples
    #      --> aliases.py     since the aliases/defines will be "Defined" only for selected samples
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


    #
    # read list of aliases
    #
    aliases = {}
    if os.path.exists(opt.aliasesFile) :
      handle = open(opt.aliasesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      aliases = {k: v for k, v in aliases.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("aliases = ", aliases)






    factory = ShapeFactory()
    factory.setValues( opt.outputDir, variables, cuts, samples, nuisances , aliases, opt.lumi)
    factory.setConditions (opt.silentMode)

    # factory._treeName  = opt.treeName
    # factory._energy    = opt.energy
    # factory._lumi      = opt.lumi
    # factory._tag       = opt.tag

    if not opt.submitBatch and not opt.haddRootFiles:
      factory.makeNominals()

    if opt.submitBatch :
      factory.submitBatch()

    if opt.haddRootFiles :
      print ("Hadd the different root files ...")

      hadd_cmd = f"hadd -j 8 -f {opt.outputDir}/root_file_joined.root    {opt.outputDir}/root_file___*.root"

      print(f"hadd: {hadd_cmd}")
      result = os.system(hadd_cmd)

      print ("I have hadded all the root files but I have not removed the original ones")
      print ("I have performed an hadd of all the suitable root files in the folder ... ")

    print ("\n\n")
    print (" I'm done ... \n\n")













