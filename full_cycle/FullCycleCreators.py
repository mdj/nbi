###########################################################################
# @Project: SFrame - ROOT-based analysis framework for ATLAS              #
#                                                                         #
# @author Stefan Ask        <Stefan.Ask@cern.ch>            - Manchester  #
# @author David Berge      <David.Berge@cern.ch>          - CERN          #
# @author Johannes Haller  <Johannes.Haller@cern.ch>      - Hamburg       #
# @author A. Krasznahorkay <Attila.Krasznahorkay@cern.ch> - CERN/Debrecen #
#                                                                         #
###########################################################################

## @package FullCycleCreators
#    @short Functions for creating a new analysis cycle torso
#
# This package collects the functions used by sframe_create_full_cycle.py
# to create the torso of a new analysis cycle. Apart from using
# sframe_create_full_cycle.py, the functions can be used in an interactive
# python session by executing:
#
# <code>
#  >>> import FullCycleCreators
# </code>

## @short Class creating analysis cycle templates
#
# This class can be used to create a template cycle inheriting from
# SCycleBase. It is quite smart actually. If you call CycleCreator.CreateCycle
# from inside an "SFrame package", it will find the right locations for the
# created files and extend an already existing LinkDef.h file with the
# line for the new cycle.


class FullCycleCreator:
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function is supposed to create an example configuration file
    # for the new cycle. It uses PyXML to write the configuration, and
    # exactly this causes a bit of trouble. PyXML is about the worst
    # XML implementation I ever came accross... There are tons of things
    # that it can't do. Not to mention the lack of any proper documentation.
    #
    # All in all, the resulting XML file is not too usable at the moment, 
    # it's probably easier just copying one of the example cycles from
    # SFrame/user/config and adjusting it to the user's needs...
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the configuration file name
    class Variable( object ):
        """
        One of the variables that will be used in the cycle.
        A variable has a name and a typename.
        A variable can be and stl-container where the input declaration must be a pointer etc.
        A variable can be commented out, in which case it will be included in the cycle, 
        but as being commented out.
        
        A list of variables is assembled either by the TreeReader directly from a root-file, 
        or by the VariableSelectionReader from a C-like file with variable declarations.
        """
        
        def __init__( self, name, typename, commented, stl_like ):
            super( FullCycleCreator.Variable, self ).__init__( )
            self.name = name
            self.typename = typename
            self.stl_like = stl_like
            self.commented = commented
        
        # End of Class Variable
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function is supposed to create an example configuration file
    # for the new cycle. It uses PyXML to write the configuration, and
    # exactly this causes a bit of trouble. PyXML is about the worst
    # XML implementation I ever came accross... There are tons of things
    # that it can't do. Not to mention the lack of any proper documentation.
    #
    # All in all, the resulting XML file is not too usable at the moment, 
    # it's probably easier just copying one of the example cycles from
    # SFrame/user/config and adjusting it to the user's needs...
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the configuration file name
    def ReadVariableSelection( self, filename ):
        """
        Reads a list of variable declarations from file into a structured format.
        From there they can be used to create the declarations and 
        connect-statements necessary to use the variables in a cycle.
        """
        varlist=[]
        try:
            text = open( filename ).read( )
        except:
            print "Unable to open variable selection file", "\"%s\"" % filename
            return varlist
        
        import re
        # Use some regexp magic to change all /*...*/ style comments to // style comments
        text=re.sub( """\*/( ?!\n)""", "*/\n", text ) # append    newline to every */
        while re.search( """/\*""", text ):  # While ther still are /* comments
            text=re.sub( """/\*(?P<line>.*?)(?P<end>\n|\*/)""", """//\g<line>/*\g<end>""", text ) # move the /* to the next newline or to the end of the comment
            text=re.sub( """/\*\*/""", "", text )  # remove zero content comments
            text=re.sub( """/\*\n""", "\n/*", text ) # move the /* past the newline
        
        # Find every variable definition.
        # Definitions may start with a //.
        # After that I expect there to be a typename of the form UInt_t or int or std::vector<double>, 
        # and finally maybe a ; and some spaces.
        for match in re.finditer( """[ \t]*(?P<comment>(?://)?)[ \t]*(?P<type>[a-zA-Z_][a-zA-Z_0-9:]*(?:[ \t]*<.+>)?)[ \t]*(?P<point>\*?)[ \t]*(?P<name>[a-zA-Z_][a-zA-Z_0-9]*)[ \t;]*""", text ):
            varargs={}
            varargs["commented"]=match.group( "comment" ) # whether the variable was commented out. Will be '//' if it was
            varargs["typename"] = match.group( "type" )
            varargs["name"] = match.group( "name" )
            varargs["stl_like"] = self.Is_stl_like( match.group( "type" ) )
            varlist.append( self.Variable( **varargs ) )
        
        return varlist
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function is supposed to create an example configuration file
    # for the new cycle. It uses PyXML to write the configuration, and
    # exactly this causes a bit of trouble. PyXML is about the worst
    # XML implementation I ever came accross... There are tons of things
    # that it can't do. Not to mention the lack of any proper documentation.
    #
    # All in all, the resulting XML file is not too usable at the moment, 
    # it's probably easier just copying one of the example cycles from
    # SFrame/user/config and adjusting it to the user's needs...
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the configuration file name
    class ROOT_Access:
        """
        A class that contains all the pyROOT related tasks.
        It will try to import pyROOT only once, and tell you if
        it failed. After that it will simply shut up and return
        empty objects if ROOT was't imported properly.
        """
        def __init__( self ):
            self.intitalized=0
        
        
        def Initalize( self ):
            if self.intitalized:
                return bool( self.ROOT )
            
            try:
                import ROOT
                self.ROOT=ROOT
            except ImportError, e:
                print "ERROR: pyROOT could not be loaded. Unable to access root-file"
                print "ERROR: You will need to supply the treename and variable list."
                print "ERROR: use -h or --help to get help."
                self.ROOT=0
            
            return bool( self.ROOT )
        
        
        def TCollIter( self, tcoll ):
            """Gives an iterator over anything that the ROOT.TIter can iterate over."""
            if not self.Initalize( ):
                return
            it=self.ROOT.TIter( tcoll )
            it.Reset( )
            item=it.Next( )
            while item:
                yield item
                item=it.Next( )
        
        
        def GetTreeName( self, rootfile ):
            """
            Get the name of the first treename in the file named rootfile.
            Or just return 'TreeName' if any errors show up.
            """
            treename= "TreeName"
            if not self.Initalize( ):
                return treename
            
            if not rootfile:
                print "No rootfile given. Using default tree name:", treename
                return treename
            
            f=self.ROOT.TFile.Open( rootfile )
            if not f:
                print rootfile, "could not be opened. Using default tree name:", treename
                return treename
            trees=[key for key in self.TCollIter( f.GetListOfKeys( ) ) if key.GetClassName( )=="TTree"]
            if len( trees ):
                treename=trees[0].GetName( )
                print "Found TTree", "\"%s\"" % treename
            f.Close( )
            
            return treename
        
        
        def ReadVars( self, rootfile, treename ):
            """
            Reads a list of variables from a root-file into a structured 
            format. From there they can be used to create the declarations and connect
            statements necessary to use the variables in a cycle.
            """
            varlist=[]
            if not self.Initalize( ):
                return varlist
            ROOT=self.ROOT
            
            if not rootfile or not treename:
                print "Incomplete arguments. Cannot get tree named \"%s\" from rootfile \"%s\"" % ( treename, rootfile )
                return varlist
            
            f=ROOT.TFile.Open( rootfile )
            if not f:
                print "Could not open root file \"%s\"" % rootfile
                return varlist
            
            tree=f.Get( treename )
            if not tree:
                print "Could not get tree \"%s\"" % treename
                f.Close( )
                return varlist
            
            for branch in self.TCollIter( tree.GetListOfBranches( ) ):
                for leaf in self.TCollIter( branch.GetListOfLeaves( ) ):
                    varargs={}
                    varargs["commented"]= ""
                    varargs["typename"] = leaf.GetTypeName( )
                    varargs["name"] = leaf.GetName( )
                    varargs["stl_like"] = FullCycleCreator.Is_stl_like( leaf.GetTypeName( ) )
                    varlist.append( FullCycleCreator.Variable( **varargs ) )
            f.Close( )
            return varlist
        
        #End of Class ROOT_Access
    
    
    ## @short Determine whether the type named by typename needs to be accessed
    # as an object or as a basic type.
    @staticmethod
    def Is_stl_like( typename ):

        #stl_like = "vector" in typename
        import re
        stl_like = bool( re.search( """<.+>""", typename ) ) or bool( "vector" in typename )
        # May want to include other stl_containers here, but I don't expect others to be used.
        # ... and really there is only so far you can go with automatic gode generation.
        if stl_like:
            return "*"
        else:
            return ""
    
    # See end of class definition for string literals
    
    def __init__( self ):
        self._headerFile = ""
        self._sourceFile = ""
        self.pyROOT=self.ROOT_Access( )
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function is supposed to create an example configuration file
    # for the new cycle. It uses PyXML to write the configuration, and
    # exactly this causes a bit of trouble. PyXML is about the worst
    # XML implementation I ever came accross... There are tons of things
    # that it can't do. Not to mention the lack of any proper documentation.
    #
    # All in all, the resulting XML file is not too usable at the moment, 
    # it's probably easier just copying one of the example cycles from
    # SFrame/user/config and adjusting it to the user's needs...
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the configuration file name
    def SplitCycleName( self, cycleName ):
        """
        splits the cycleName into a class name and a namespace name
        returns a tuple of (namespace, className )
        """
        namespace=""
        className=cycleName
        import re
        if re.search( "::", cycleName ):
            m = re.match( "(.*)::(.*)", cycleName )
            namespace = m.group( 1 )
            className = m.group( 2 )
        
        return ( namespace, className )
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function is supposed to create an example configuration file
    # for the new cycle. It uses PyXML to write the configuration, and
    # exactly this causes a bit of trouble. PyXML is about the worst
    # XML implementation I ever came accross... There are tons of things
    # that it can't do. Not to mention the lack of any proper documentation.
    #
    # All in all, the resulting XML file is not too usable at the moment, 
    # it's probably easier just copying one of the example cycles from
    # SFrame/user/config and adjusting it to the user's needs...
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the configuration file name
    def Backup( self, filename ):
        """
        Check if the file exists. If it does, beck it up to file+".backup"
        """
        import os.path
        if os.path.exists( filename ):
            print "WARNING:: File \"%s\" already exists" % filename
            print "WARNING:: Moving \"%s\" to \"%s.backup\"" % ( filename, filename )
            import shutil
            shutil.move( filename, filename + ".backup" )
            

    ## @short Function creating an analysis cycle header
    #
    # This function can be used to create the header file for a new analysis
    # cycle.
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the output header file name
    # @param namespace  Optional parameter with the name of the namespace to use
    # @param varlist  Optional parameter with a list of "Variable" objects for which to create declarations
    # @param create_output  Optional parameter for whether to create declarations for output variables
    def CreateHeader( self, className, fileName = "" , namespace="", varlist=[], create_output=False ):
        # Construct the file name if it has not been specified:
        if  not fileName:
            fileName = className + ".h"
        
        fullClassName=className
        if namespace:
            fullClassName=namespace+"::"+className
        formdict={"tab":self._tab, "class":className, "namespace":namespace, "fullClassName":fullClassName}

        # Now create all the lines to declare the input and output variables
        inputVariableDeclarations=""
        outputVariableDeclarations=""

        for var in varlist:
            subs_dict=dict( formdict )
            subs_dict.update( var.__dict__ )
            inputVariableDeclarations += "%(tab)s%(commented)s%(typename)s\t%(stl_like)s%(name)s;\n" % subs_dict

            if create_output:
                outputVariableDeclarations += "%(tab)s%(commented)s%(typename)s\tout_%(name)s;\n" % subs_dict
        
        formdict["inputVariableDeclarations"]=inputVariableDeclarations
        formdict["outputVariableDeclarations"]=outputVariableDeclarations
        # Some printouts:
        print "CreateHeader:: Cycle name     = " + className
        print "CreateHeader:: File name      = " + fileName
        self._headerFile = fileName

        # Create a backup of an already existing header file:
        self.Backup( fileName )
        
        # Construct the contents:
        body=self._Template_header_Body % formdict
        if namespace:
            ns_body=self._Template_namespace % {"namespace":namespace, "body":re.sub( """(?:^|\n)(?=.)""", """\g<0>%s"""%self._tab, body )}
        else:
            ns_body=body
        import re
        full_contents=self._Template_header_Frame % {"body":ns_body, "class":( namespace+"_"+className ).upper( ), "fullClassName":namespace+"::"+className}

        # Write the header file:
        output = open( fileName, "w" )
        output.write( full_contents )
        output.close( )
        
        return fileName
    
    
    ## @short Function creating the analysis cycle source file
    #
    # This function creates the source file that works with the header created
    # by CreateHeader. It is important that CreateHeader is executed before
    # this function, as it depends on knowing where the header file is
    # physically. (To include it correctly in the source file.)
    #
    # @param className Name of the analysis cycle
    # @param fileName  Optional parameter with the output source file name
    # @param namespace  Optional parameter with the name of the namespace to use
    # @param varlist  Optional parameter with a list of "Variable" objects to be used by the cycle
    # @param create_output  Optional parameter for whether to produce code for output variables
    def CreateSource( self, className, fileName = "", namespace="", varlist=[], create_output=False, header="" ):
        # Construct the file name if it has not been specified:
        if fileName == "":
            fileName = className + ".cxx"
        
        if not header:
            header= className + ".h"
        
        fullClassName=className
        if namespace:
            fullClassName=namespace+"::"+className
        formdict={"tab":self._tab, "class":className, "namespace":namespace, "fullClassName":fullClassName}
        
        # Determine the relative path of the header
        import os
        headpath = os.path.dirname( os.path.abspath( header ) ).split( os.sep )
        srcpath = os.path.dirname( os.path.abspath( fileName ) ).split( os.sep )
        #find the indx from which the paths differ:
        index=0
        while index < min( len( headpath ), len( srcpath ) ) and headpath[index]==srcpath[index]:
            index+=1
        
        if index==0:
            include=os.path.abspath( header )
        else:
            # Step down the path of the Source-file
            path = [ ".." for directory in srcpath[index:] ]
            # and up the path of the header
            path += headpath[index:]
            include = os.path.join( os.sep.join( path ), os.path.basename( header ) )
        
        # Now create all the lines to handle the variables
        inputVariableConnections=""
        outputVariableConnections=""
        outputVariableClearing=""
        outputVariableFilling=""

        for var in varlist:
            subs_dict=dict( formdict )
            subs_dict.update( var.__dict__ )

            inputVariableConnections += "%(tab)s%(commented)sConnectVariable( InTreeName.c_str(), \"%(name)s\", %(name)s );\n" % subs_dict

            if create_output:
                outputVariableConnections += "%(tab)s%(commented)sDeclareVariable( out_%(name)s, \"%(name)s\" );\n" % subs_dict
                outputVariableFilling += "%(tab)s%(commented)sout_%(name)s = %(stl_like)s%(name)s;\n" % subs_dict
                if var.stl_like:
                    outputVariableClearing += "%(tab)s%(commented)sout_%(name)s.clear();\n" % subs_dict
        
        formdict["inputVariableConnections"]=inputVariableConnections
        formdict["outputVariableConnections"]=outputVariableConnections
        formdict["outputVariableClearing"]=outputVariableClearing
        formdict["outputVariableFilling"]=outputVariableFilling
        
        # Some printouts:
        print "CreateSource:: Cycle name     = " + className
        print "CreateSource:: File name      = " + fileName
        self._sourceFile = fileName

        
        # Create a backup of an already existing source file:
        self.Backup( fileName )
        
        #Construct the contents of the source file:
        body=self._Template_source_Body % formdict
        if namespace:
            import re
            ns_body=self._Template_namespace % {"namespace":namespace, "body":re.sub( """(?:^|\n)(?=.)""", """\g<0>%s"""%self._tab, body )}
        else:
            ns_body=body
        full_contents=self._Template_source_Frame % {"body":ns_body, "fullClassName":fullClassName, "header":include}
        
        
        # Write the source file:
        output = open( fileName, "w" )
        output.write( full_contents )
        output.close( )
        return
    
    
    ## @short Function adding link definitions for rootcint
    #
    # Each new analysis cycle has to declare itself in a so called "LinkDef
    # file". This makes sure that rootcint knows that a dictionary should
    # be generated for this C++ class.
    #
    # This function is also quite smart. If the file name specified does
    # not yet exist, it creates a fully functionaly LinkDef file. If the
    # file already exists, it just inserts one line declaring the new
    # cycle into this file.
    #
    # @param className Name of the analysis cycle. Can contain the namespace name.
    # @param fileName  Optional parameter with the LinkDef file name
    # @param namespace  Optional parameter with the name of the namespace to use
    def AddLinkDef( self, className, fileName = "LinkDef.h" , namespace="", varlist=[] ):
        
        cycleName=className
        if namespace:
            cycleName=namespace+"::"+className
        
        new_lines="#pragma link C++ class %s+;\n" %  cycleName
        
        types=set( )
        for var in varlist:
            if self.Is_stl_like( var.typename ):
                types.add( var.typename )
        
        for typename in types:
            new_lines+="#pragma link C++ class %s+;\n" % typename
        
        import os.path
        if os.path.exists( fileName ):
            print "AddLinkDef:: Extending already existing file \"%s\"" % fileName
            # Read in the already existing file:
            infile = open( fileName, "r" )
            text=infile.read( )
            infile.close( )

            # Find the "#endif" line:
            import re
            if not re.search( """#endif""", text ):
                print "AddLinkDef:: ERROR File \"%s\" is not in the right format!" % fileName
                print "AddLinkDef:: ERROR Not adding link definitions!"
                return
            
            # Overwrite the file with the new contents:
            output = open( fileName, "w" )
            output.write( re.sub( """(?=\n#endif)""", new_lines+"\n", text ) )
            output.close( )

        else:
            # Create a new file and fill it with all the necessary lines:
            print "AddLinkDef:: Creating new file called \"%s\"" % fileName
            output = open( fileName, "w" )
            output.write( self._Template_LinkDef %{"new_lines":new_lines} )

        return
    
    
    ## @short Function creating a configuration file for the new cycle
    #
    # This function uses the configuration file in $SFRAME_DIR/user/config/FirstCycle_config.xml
    # and adapts it for this analysis using PyXML. As this file is expected to
    # change in future updates this function may break. It may therefore be better to create something from scratch.
    # The advantage of this approach is that the resulting xml file works, and still
    # contains all the comments of FirstCycle_config.xml, making it more usable.
    # 
    #
    # @param className Name of the analysis cycle
    # @param fileName  Optional parameter with the output source file name
    # @param namespace  Optional parameter with the name of the namespace to use
    # @param analysis  Optional parameter with the name of the analysis package
    # @param rootfile  Optional parameter with the name of an input root-file
    # @param treename  Optional parameter with the name of the input tree
    # @param outtree  Optional parameter with the name of the output tree if desired
    def CreateConfig( self, className, fileName = "" , namespace="ns", analysis="MyAnalysis", rootfile="my/root/file.root", treename="InTreeName", outtree="" ):
        # Construct the file name if it has not been specified:
        if fileName == "":
            fileName = className + "_config.xml"
        self.Backup( fileName )
        
        cycleName=className
        if namespace:
            cycleName=namespace+"::"+cycleName
        
        # Some printouts:
        print "CreateConfig:: Cycle name     = " + className
        print "CreateConfig:: File name      = " + fileName

        # Use the configuration file FirstCycle_config.xml as a basis:
        import os
        xmlinfile=os.path.join( os.getenv( "SFRAME_DIR" ), "user/config/FirstCycle_config.xml" )
        if not os.path.exists( xmlinfile ):
            print "ERROR: Expected to find example configuration at", xmlinfile
            print "ERROR: No configuration file will be written."
            return

        import xml.dom.minidom
        example_xml=open( xmlinfile )
        dom=xml.dom.minidom.parse( example_xml )
        example_xml.close( )
        
        #Make the necessary changes to adapt this file to our purposes
        try:
            nodes=dom.getElementsByTagName( "JobConfiguration" )
            if not len( nodes )==1: raise AssertionError
            nodes[0].setAttribute( "JobName", className+"Job" )
            nodes[0].setAttribute( "OutputLevel", "INFO" )

            for node in dom.getElementsByTagName( "Library" ):
                if node.getAttribute( "Name" )=="libSFrameUser":
                    node.setAttribute( "Name", "lib"+analysis )

            for node in dom.getElementsByTagName( "Package" ):
                if node.getAttribute( "Name" )=="SFrameUser.par":
                    node.setAttribute( "Name", analysis+".par" )

            nodes=dom.getElementsByTagName( "Cycle" )
            if not len( nodes )==1: raise AssertionError
            cycle=nodes[0]
            cycle.setAttribute( "Name", cycleName )
            cycle.setAttribute( "RunMode", "LOCAL" )

            nodes=cycle.getElementsByTagName( "InputData" )
            while len( dom.getElementsByTagName( "InputData" ) )>1:
                cycle.removeChild( dom.getElementsByTagName( "InputData" )[0] )

            inputData=dom.getElementsByTagName( "InputData" )[0]
            inputData.setAttribute( "Lumi", "1.0" )
            inputData.setAttribute( "Version", "V1" )
            inputData.setAttribute( "Type", "DATA" )

            while len( inputData.getElementsByTagName( "In" ) )>1:
                inputData.removeChild( inputData.getElementsByTagName( "In" )[0] )
            In=inputData.getElementsByTagName( "In" )[0]
            In.setAttribute( "Lumi", "1.0" )
            In.setAttribute( "FileName", rootfile )

            while len( inputData.getElementsByTagName( "InputTree" ) )>1:
                inputData.removeChild( inputData.getElementsByTagName( "InputTree" )[0] )
            inputData.getElementsByTagName( "InputTree" )[0].setAttribute( "Name", treename )

            while len( inputData.getElementsByTagName( "MetadataOutputTree" ) ):
                inputData.removeChild( inputData.getElementsByTagName( "MetadataOutputTree" )[0] )

            while len( inputData.getElementsByTagName( "OutputTree" ) )>1:
                inputData.removeChild( inputData.getElementsByTagName( "OutputTree" )[0] )
            outtreenode=inputData.getElementsByTagName( "OutputTree" )[0]
            if not outtree:
                inputData.removeChild( outtreenode )
            else:
                outtreenode.setAttribute( "Name", outtree )

            nodes=cycle.getElementsByTagName( "UserConfig" )
            if not len( nodes )==1: raise AssertionError
            UserConfig=nodes[0]

            while len( UserConfig.getElementsByTagName( "Item" ) )>1:
                UserConfig.removeChild( UserConfig.getElementsByTagName( "Item" )[0] )
            Item=UserConfig.getElementsByTagName( "Item" )[0]
            Item.setAttribute( "Name", "InTreeName" )
            Item.setAttribute( "Value", treename )
        except AssertionError, e:
            print "ERROR: ", xmlinfile, "has an unexpected structure."
            print "ERROR: No configuration file will be written."
            return

        import re
        text=re.sub( """(?<=\n)([ \t]*\n)+""", "", dom.toprettyxml( encoding="UTF-8" ) ) #remove empty lines

        outfile=open( fileName, "w" )
        outfile.write( text )
        return
    
    
    ## @short Function to add a JobConfig file to the analysis
    #
    # A JobConfig.dtd file is necessary for parsing the config xml files.
    # Use the one from the $SFRAME_DIR/user/ example if there isn't one 
    # here already.
    #
    # @param directory The name of the directory where the file should be
    def AddJobConfig( self, directory ):
        import os.path
        newfile=os.path.join( directory, "JobConfig.dtd" )
        if os.path.exists( newfile ):
            print "Keeping existing JobConfig.dtd"
            return
        
        oldfile=os.path.join( os.getenv( "SFRAME_DIR" ), "user/config/JobConfig.dtd" )
        if not os.path.exists( oldfile ):
            print "ERROR: Expected JobConfig.dtd file at", oldfile
            print "ERROR: JobConfig.dtd file not copied"
            
        import shutil
        shutil.copy( oldfile, newfile )
        print "Using a copy of", oldfile
    
    
    ## @short Main analysis cycle creator function
    #
    # The users of this class should normally just use this function
    # to create a new analysis cycle.
    #
    # It only really needs to receive the name of the new cycle, it can guess
    # the values of all the oter parameters. It calls all the
    # other functions of this class to create all the files for the new
    # cycle.
    #
    # @param cycleName Name of the analysis cycle. Can contain the namespace name.
    # @param linkdef Optional parameter with the name of the LinkDef file
    # @param rootfile Optional parameter with the name of a rootfile containing a TTree
    # @param treename Optional parameter with the name of the input TTree
    # @param varlist Optional parameter with a filename for a list of desired variable declarations
    # @param outtree Optional parameter with the name of the output TTree
    # @param analysis Optional parameter with the name of analysis package
    def CreateCycle( self, cycleName, linkdef = "", rootfile = "", treename = "", varlist = "", outtree="", analysis="" ):
        
        namespace, className=self.SplitCycleName( cycleName )
        
        if not analysis:
            import os
            analysis=os.path.basename( os.getcwd( ) )
            print "Using analysis name", "\"%s\"" % analysis
        
        #First we take care of all the variables that the user may want to have read in.
        # If treename wasn't given, it can be read from the rootfile if it exits.
        if not treename:
            treename=self.pyROOT.GetTreeName( rootfile ) # gives default if rootfile is empty
        
        # The three parameters related to the input variables are varlist, treename and rootfile.
        # if neither rootfile or varlist are given, no input variable code will be written.
        cycle_variables=[]
        if rootfile or varlist:
            # Prefer to read the input from the varlist
            if varlist:
                cycle_variables=self.ReadVariableSelection( varlist )
            elif rootfile:
                cycle_variables=self.pyROOT.ReadVars( rootfile, treename )
        
        # The list of input variables is now contained in cycle_variables
        # if this list is empty, the effect of this class should be identical to that of the old CycleCreators
        
        #From now on rootfile is only used in the config file:
        if not rootfile:
            rootfile="your/input/file.root"
        
        formdict={"tab":self._tab, "className":className, "cycleName":cycleName, "namespace":namespace}
        
        # Check if a directory called "include" exists in the current directory.
        # If it does, put the new header in that directory. Otherwise leave it up
        # to the CreateHeader function to put it where it wants.
        import os.path
        include_dir="./include/"
        if not os.path.exists( include_dir ):
            include_dir=""
            
        if not linkdef:
            import glob
            filelist = glob.glob( include_dir+"*LinkDef.h" )
            if len( filelist ) == 0:
                print "CreateCycle:: WARNING There is no LinkDef file under", include_dir
                linkdef = include_dir+"LinkDef.h"
                print "CreateCycle:: WARNING Creating one with the name", linkdef
            elif len( filelist ) == 1:
                linkdef = filelist[ 0 ]
            else:
                print "CreateCycle:: ERROR Multiple header files ending in LinkDef.h"
                print "CreateCycle:: ERROR I don't know which one to use..."
                return
        
        # Check if a directory called "src" exists in the current directory.
        # If it does, put the new source in that directory. Otherwise leave it up
        # to the CreateSource function to put it where it wants.
        src_dir="./src/"
        if not os.path.exists( src_dir ):
            src_dir=""

        # Check if a directory called "config" exists in the current directory.
        # If it does, put the new configuration in that directory. Otherwise leave it up
        # to the CreateConfig function to put it where it wants.
        config_dir="./config/"
        if not os.path.exists( config_dir ):
            config_dir=""
        
        
        # All options seem to be in order. Generate the code.
        header=self.CreateHeader( className, include_dir + className + ".h", namespace=namespace, varlist=cycle_variables, create_output=bool( outtree ) )
        self.AddLinkDef( className, linkdef , namespace=namespace, varlist=cycle_variables )
        self.CreateSource( className, src_dir + className + ".cxx", namespace=namespace, varlist=cycle_variables, create_output=bool( outtree ), header=header )
        self.CreateConfig( className, fileName=config_dir + className + "_config.xml" , namespace=namespace, analysis=analysis, rootfile=rootfile, treename=treename, outtree=outtree )
        self.AddJobConfig( directory=config_dir )
        return
    
    # End of function declarations
    # From now on there are declarations of the string templates that produce the code.
    
    ## @short The Tab character
    #
    # Define the tab character to be used during code gerneration
    # may be, for example, "\t", "  ", "   " or "    "
    _tab=" "*4
    # _headerFile = ""
    # _sourceFile = ""
    
    ## @short Template for namespaced code
    #
    # This string is used to enclose code bodys in a namespace
    _Template_namespace="namespace %(namespace)s {\n\n%(body)s\n\n}\n"

    ## @short Template for the body of a header file
    #
    # This string is used by CreateHeader to create the body of a header file
    _Template_header_Body = """
/**
 *    @short Put short description of class here
 *
 *          Put a longer description over here...
 *
 *  @author Put your name here
 * @version $Revision: 173 $
 */
class %(class)-s : public SCycleBase {

public:
    /// Default constructor
    %(class)-s();
    /// Default destructor
    ~%(class)-s();

    /// Function called at the beginning of the cycle
    virtual void BeginCycle() throw( SError );
    /// Function called at the end of the cycle
    virtual void EndCycle() throw( SError );

    /// Function called at the beginning of a new input data
    virtual void BeginInputData( const SInputData& ) throw( SError );
    /// Function called after finishing to process an input data
    virtual void EndInputData  ( const SInputData& ) throw( SError );

    /// Function called after opening each new input file
    virtual void BeginInputFile( const SInputData& ) throw( SError );

    /// Function called for every event
    virtual void ExecuteEvent( const SInputData&, Double_t ) throw( SError );

private:
    //
    // Put all your private variables here
    //
    string InTreeName;
    
    // Input Variables
%(inputVariableDeclarations)s

    //Output Variables
%(outputVariableDeclarations)s

    // Macro adding the functions for dictionary generation
    ClassDef( %(fullClassName)s, 0 );

}; // class %(class)-s
"""

    ## @short Template for a header file
    #
    # This string is used by CreateHeader to create a header file
    # once the body has already been generated
    _Template_header_Frame = """// Dear emacs, this is -*- c++ -*-
#ifndef %(class)-s_H
#define %(class)-s_H

// SFrame include(s):
#include \"core/include/SCycleBase.h\"
#include <vector>
#include <string>
using namespace std;

%(body)s

#endif // %(class)-s_H

"""
    ## @short Template for the body of a source file
    #
    # This string is used by CreateSource to create the body of a source file
    _Template_source_Body = """
%(class)-s::%(class)-s()
    : SCycleBase() {
    
    DeclareProperty("InTreeName", InTreeName );
    SetLogName( GetName() );
}

%(class)-s::~%(class)-s() {

}

void %(class)-s::BeginCycle() throw( SError ) {

    return;

}

void %(class)-s::EndCycle() throw( SError ) {

    return;

}

void %(class)-s::BeginInputData( const SInputData& ) throw( SError ) {

%(outputVariableConnections)s
    return;

}

void %(class)-s::EndInputData( const SInputData& ) throw( SError ) {

    return;

}

void %(class)-s::BeginInputFile( const SInputData& ) throw( SError ) {

%(inputVariableConnections)s
    return;

}

void %(class)-s::ExecuteEvent( const SInputData&, Double_t ) throw( SError ) {

%(outputVariableClearing)s

    // The main part of your analysis goes here
    
%(outputVariableFilling)s

    return;

}
"""

    ## @short Template for the frame of a source file
    #
    # This string is used by CreateSource to create a source file
    # once the main body has already been generated
    _Template_source_Frame = """
// Local include(s):
#include \"%(header)s\"

ClassImp( %(fullClassName)s );

%(body)s
"""
    _Template_LinkDef="""// Dear emacs, this is -*- c++ -*-

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link C++ nestedclass;

%(new_lines)s
#endif // __CINT__
"""