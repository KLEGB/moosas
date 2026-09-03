// {{MadCap}} //////////////////////////////////////////////////////////////////
// Copyright: MadCap Software, Inc - www.madcapsoftware.com ////////////////////
////////////////////////////////////////////////////////////////////////////////
// <version>4.2.0.0</version>
////////////////////////////////////////////////////////////////////////////////

var gLoaded					= false;
var gReadyFuncs				= new Array();
var gOnloadFuncs			= new Array();
var gPreviousOnloadFunction	= window.onload;
var gReady					= false;

if ( gPreviousOnloadFunction != null )
{
	gOnloadFuncs.push( gPreviousOnloadFunction );
}

window.onload = function()
{
	for ( var i = 0; i < gReadyFuncs.length; i++ )
	{
		gReadyFuncs[i]();
	}
	
	gReady = true;
	
	MCGlobals.Init();
	
	FMCRegisterCallback( "MCGlobals", MCEventType.OnInit, OnMCGlobalsInit, null );
};

function OnMCGlobalsInit( args )
{
	for ( var i = 0; i < gOnloadFuncs.length; i++ )
	{
		gOnloadFuncs[i]();
	}
	
	gLoaded = true;
}

var MCGlobals	= new function()
{
	// Private member variables
	
	var mSelf	= this;
	
	// Public properties

	this.SubsystemFile		= "ContamHelp.xml";
	this.SkinFolder			= "Data/Skinmain/";
	this.SkinTemplateFolder	= "Skin/";
	this.DefaultStartTopic	= "html/SketchPad/IDH_UsingSketchPad_WorkingWithTheSketchPad.htm";
	this.InPreviewMode  	= false;
	
	this.Initialized		= false;
	
	this.RootFolder				= null;
	this.RootFrame				= null;
	this.ToolbarFrame			= null;
	this.BodyFrame				= null;
	this.NavigationFrame		= null;
	this.TopicCommentsFrame		= null;
	this.RecentCommentsFrame	= null;
	this.BodyCommentsFrame		= null;
	this.PersistenceFrame		= null;
	
	// Private methods
	
	function InitRoot()
	{
		mSelf.RootFrame = window;
		mSelf.ToolbarFrame = frames["mctoolbar"];
		mSelf.BodyFrame = frames["body"];
		mSelf.NavigationFrame = frames["navigation"];
		mSelf.PersistenceFrame = null;
		
		//
		
		var bodyReady	= false;
		
		FMCRegisterCallback( "Navigation", MCEventType.OnReady, OnNavigationReady, null );
		
		function OnNavigationReady( args )
		{
			mSelf.TopicCommentsFrame = mSelf.NavigationFrame.frames["topiccomments"];
			mSelf.RecentCommentsFrame = mSelf.NavigationFrame.frames["recentcomments"];
			
			//
			
			if ( bodyReady )
			{
				mSelf.Initialized = true;
			}
		}
		
		FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
		function OnBodyReady( args )
		{
			mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
			
			//
			
			bodyReady = true;
			
			if ( mSelf.TopicCommentsFrame != null )
			{
				mSelf.Initialized = true;
			}
		}
	}
	
	function InitTopicCHM()
	{
		mSelf.RootFrame = null;
		mSelf.ToolbarFrame = frames["mctoolbar"];
		mSelf.BodyFrame = window;
		mSelf.NavigationFrame = null;
		mSelf.TopicCommentsFrame = null;
		mSelf.RecentCommentsFrame = null;
		mSelf.BodyCommentsFrame = frames["topiccomments"];
		mSelf.PersistenceFrame = frames["persistence"];
		
		//
			
		mSelf.Initialized = true;
	}
	
	function InitNavigation()
	{
		mSelf.RootFrame = parent;
		mSelf.NavigationFrame = window;
		mSelf.TopicCommentsFrame = frames["topiccomments"];
		mSelf.RecentCommentsFrame = frames["recentcomments"];
		mSelf.PersistenceFrame = null;
		
		FMCRegisterCallback( "Root", MCEventType.OnReady, OnRootReady, null );
			
		function OnRootReady( args )
		{
			mSelf.ToolbarFrame = mSelf.RootFrame.frames["mctoolbar"];
			mSelf.BodyFrame = mSelf.RootFrame.frames["body"];
			
			var bodyReady	= false;
			var rootLoaded	= false;
			
			FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
			function OnBodyReady( args )
			{
				bodyReady = true;
				
				mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
				
				//
				
				if ( FMCIsWebHelpAIR() )
				{
					if ( rootLoaded )
					{
						mSelf.Initialized = true;
					}
				}
				else
				{
					mSelf.Initialized = true;
				}
			}
			
			if ( FMCIsWebHelpAIR() )
			{
				FMCRegisterCallback( "Root", MCEventType.OnLoad, OnRootLoaded, null );
				
				function OnRootLoaded( args )
				{
					rootLoaded = true;
					
					if ( bodyReady )
					{
						mSelf.Initialized = true;
					}
				}
			}
		}
	}
	
	function InitNavigationFramesWebHelp()
	{
		var bodyReady	= false;
		
		mSelf.RootFrame = parent.parent;
		mSelf.NavigationFrame = parent;
		mSelf.PersistenceFrame = null;
		
		FMCRegisterCallback( "Root", MCEventType.OnReady, OnRootReady, null );
			
		function OnRootReady( args )
		{
			mSelf.ToolbarFrame = mSelf.RootFrame.frames["mctoolbar"];
			mSelf.BodyFrame = mSelf.RootFrame.frames["body"];
			
			FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
			function OnBodyReady( args )
			{
				mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
				
				//
				
				bodyReady = true;
				
				if ( window.name == "search" && FMCIsWebHelpAIR() )
				{
					if ( window.parentSandboxBridge != null )
					{
						mSelf.Initialized = true;
					}
				}
				else
				{
					if ( mSelf.TopicCommentsFrame != null )
					{
						mSelf.Initialized = true;
					}
				}
			}
		}
		
		FMCRegisterCallback( "Navigation", MCEventType.OnReady, OnNavigationReady, null );
			
		function OnNavigationReady( args )
		{
			mSelf.TopicCommentsFrame = mSelf.NavigationFrame.frames["topiccomments"];
			mSelf.RecentCommentsFrame = mSelf.NavigationFrame.frames["recentcomments"];
			
			if ( window.name == "search" && FMCIsWebHelpAIR() )
			{
				FMCRegisterCallback( "Navigation", MCEventType.OnLoad, OnNavigationLoaded, null );
				
				function OnNavigationLoaded( args )
				{
					if ( bodyReady )
					{
						mSelf.Initialized = true;
					}
				}
			}
			else
			{
				if ( bodyReady )
				{
					mSelf.Initialized = true;
				}
			}
		}
	}
	
	function InitBodyCommentsFrameWebHelp()
	{
		mSelf.RootFrame = parent.parent;
		mSelf.NavigationFrame = parent.parent.frames["navigation"];
		mSelf.PersistenceFrame = null;
		mSelf.ToolbarFrame = parent.parent.frames["mctoolbar"];
		mSelf.BodyFrame = parent;
		mSelf.BodyCommentsFrame = window;
		
		FMCRegisterCallback( "Navigation", MCEventType.OnReady, OnNavigationReady, null );
			
		function OnNavigationReady( args )
		{
			mSelf.TopicCommentsFrame = mSelf.NavigationFrame.frames["topiccomments"];
			mSelf.RecentCommentsFrame = mSelf.NavigationFrame.frames["recentcomments"];
			
			//
			
			mSelf.Initialized = true;
		}
	}
	
	function InitBodyCommentsFrameDotNetHelp()
	{
		mSelf.RootFrame = null;
		mSelf.ToolbarFrame = null;
		mSelf.BodyFrame = parent;
		mSelf.NavigationFrame = null;
		mSelf.TopicCommentsFrame = null;
		mSelf.RecentCommentsFrame = null;
		mSelf.BodyCommentsFrame = window;
		mSelf.PersistenceFrame = null;

		//

		mSelf.Initialized = true;
	}
	
	function InitToolbarWebHelp()
	{
		mSelf.RootFrame = parent;
		mSelf.ToolbarFrame = window;
		mSelf.PersistenceFrame = null;
		
		FMCRegisterCallback( "Root", MCEventType.OnReady, OnRootReady, null );
			
		function OnRootReady( args )
		{
			mSelf.BodyFrame = mSelf.RootFrame.frames["body"];
			mSelf.NavigationFrame = mSelf.RootFrame.frames["navigation"];
			
			//
			
			var bodyReady	= false;
			
			FMCRegisterCallback( "Navigation", MCEventType.OnReady, OnNavigationReady, null );
			
			function OnNavigationReady( args )
			{
				mSelf.TopicCommentsFrame = mSelf.NavigationFrame.frames["topiccomments"];
				mSelf.RecentCommentsFrame = mSelf.NavigationFrame.frames["recentcomments"];
				
				//
				
				if ( bodyReady )
				{
					mSelf.Initialized = true;
				}
			}
			
			FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
			function OnBodyReady( args )
			{
				mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
				
				//
				
				bodyReady = true;
				
				if ( mSelf.TopicCommentsFrame != null )
				{
					mSelf.Initialized = true;
				}
			}
		}
	}
	
	function InitToolbarCHM()
	{
		mSelf.RootFrame = null;
		mSelf.ToolbarFrame = window;
		mSelf.BodyFrame = parent;
		mSelf.NavigationFrame = null;
		mSelf.TopicCommentsFrame = null;
		mSelf.RecentCommentsFrame = null;
		
		FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
		function OnBodyReady( args )
		{
			mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
			mSelf.PersistenceFrame = mSelf.BodyFrame.frames["persistence"];
			
			//
		
			mSelf.Initialized = true;
		}
	}
	
	function InitTopicWebHelp()
	{
		mSelf.RootFrame = parent;
		mSelf.BodyFrame = window;
		mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
		mSelf.PersistenceFrame = null;
		
		FMCRegisterCallback( "Root", MCEventType.OnReady, OnRootReady, null );
		
		function OnRootReady( args )
		{
			mSelf.ToolbarFrame = mSelf.RootFrame.frames["mctoolbar"];
			mSelf.NavigationFrame = mSelf.RootFrame.frames["navigation"];
			
			var rootLoaded	= false;
			
			FMCRegisterCallback( "Navigation", MCEventType.OnReady, OnNavigationReady, null );
			
			function OnNavigationReady( args )
			{
				mSelf.TopicCommentsFrame = mSelf.NavigationFrame.frames["topiccomments"];
				mSelf.RecentCommentsFrame = mSelf.NavigationFrame.frames["recentcomments"];
				
				//
			
				if ( FMCIsWebHelpAIR() )
				{
					if ( rootLoaded )
					{
						mSelf.Initialized = true;
					}
				}
				else
				{
					mSelf.Initialized = true;
				}
			}
			
			if ( FMCIsWebHelpAIR() )
			{
				FMCRegisterCallback( "Root", MCEventType.OnLoad, OnRootLoaded, null );
				
				function OnRootLoaded( args )
				{
					rootLoaded = true;
					
					if ( mSelf.TopicCommentsFrame != null )
					{
						mSelf.Initialized = true;
					}
				}
			}
		}
	}
	
	function InitTopicDotNetHelp()
	{
		mSelf.RootFrame = null;
		mSelf.ToolbarFrame = null;
		mSelf.BodyFrame = window;
		mSelf.NavigationFrame = null;
		mSelf.TopicCommentsFrame = null;
		mSelf.RecentCommentsFrame = null;
		mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
		mSelf.PersistenceFrame = null;

		//

		mSelf.Initialized = true;
	}
	
	function InitNavigationFramesCHM()
	{
		mSelf.RootFrame = null;
		mSelf.BodyFrame = parent;
		mSelf.NavigationFrame = null;
		mSelf.TopicCommentsFrame = null;
		
		FMCRegisterCallback( "Body", MCEventType.OnReady, OnBodyReady, null );
			
		function OnBodyReady( args )
		{
			mSelf.ToolbarFrame = mSelf.BodyFrame.frames["mctoolbar"];
			mSelf.RecentCommentsFrame = mSelf.BodyFrame.frames["recentcomments"];
			mSelf.BodyCommentsFrame = mSelf.BodyFrame.frames["topiccomments"];
			mSelf.PersistenceFrame = mSelf.BodyFrame.frames["persistence"];
			
			//
		
			mSelf.Initialized = true;
		}
	}
	
	// Public methods
	
	this.Init	= function()
	{
		if ( FMCInPreviewMode() )
		{
			mSelf.Initialized = true;
			
			return;
		}
		
		if ( window.name == "bridge" )
		{
			mSelf.Initialized = true;
			
			return;
		}
		else if ( frames["mctoolbar"] != null )	// Root or topic in CHM
		{
			mSelf.ToolbarFrame = frames["mctoolbar"];
			
			if ( frames["body"] != null )	// Root
			{
				InitRoot();
			}
			else							// Topic in CHM
			{
				InitTopicCHM();
			}
		}
		else if ( window.name == "navigation" )	// Navigation
		{
			InitNavigation();
		}
		else if ( parent.name == "navigation" )	// Navigation frames in WebHelp
		{
			InitNavigationFramesWebHelp();
		}
		else if ( window.name == "mctoolbar" )	// Toolbar
		{
			mSelf.ToolbarFrame = window;
			
			if ( parent.frames["navigation"] != null )	// Toolbar in WebHelp
			{
				InitToolbarWebHelp();
			}
			else										// Toolbar in CHM
			{
				InitToolbarCHM();
			}
		}
		else if ( window.name == "body" )	// Topic in WebHelp
		{
			if ( FMCIsWebHelp() )
			{
				InitTopicWebHelp();
			}
			else if ( FMCIsDotNetHelp() )
			{
				InitTopicDotNetHelp();
			}
			else if ( FMCIsHtmlHelp() )
			{
				InitTopicCHM();
			}
		}
		else if ( window.name == "topiccomments" )
		{
			if ( parent.name != "body" )
			{
				mSelf.Initialized = true;
				
				return;
			}
			
			if ( FMCIsHtmlHelp() )
			{
				InitNavigationFramesCHM();	// Body comments frame in CHM
			}
			else if ( FMCIsWebHelp() )
			{
				InitBodyCommentsFrameWebHelp();	// Body comments frame in WebHelp body
			}
			else if ( FMCIsDotNetHelp() )
			{
				InitBodyCommentsFrameDotNetHelp();	// Body comments frame in DotNet Help body
			}
		}
		else if (	window.name == "toc" ||
					window.name == "index" ||
					window.name == "search" ||
					window.name == "glossary" ||
					window.name == "favorites" ||
					window.name == "browsesequences" ||
					window.name == "recentcomments" )	// Navigation frames in CHM
		{
			InitNavigationFramesCHM();
		}
		else if ( FMCIsTopicPopup( window ) )   // Topic popup
		{
			var currFrame	= window;
			
			while ( true )
			{
				if ( currFrame.frames["navigation"] != null )
				{
					mSelf.RootFrame = currFrame;
					
					break;
				}
				
				if ( currFrame.parent == currFrame )
				{
					break;
				}
				
				currFrame = currFrame.parent;
			}
			
            mSelf.Initialized = true;
		}
		else if ( FMCIsDotNetHelp() )
		{
			mSelf.Initialized = true;
		}
		else
		{
			mSelf.Initialized = true;
			
			return;
		}
		
		if ( FMCIsWebHelp() )
		{
			var rootFolder	= new CMCUrl( mSelf.RootFrame.document.location.href ).ToFolder();
			var href		= new CMCUrl( document.location.href );
			var subFolder	= href.ToFolder().ToRelative( rootFolder );
			
			if ( subFolder.FullPath.StartsWith( "Subsystems", false ) )
			{
				while ( subFolder.FullPath.StartsWith( "Subsystems", false ) )
				{
					rootFolder = rootFolder.AddFile( "Subsystems/" );
					subFolder = href.ToFolder().ToRelative( rootFolder );
					
					var projFolder = subFolder.FullPath.substring( 0, subFolder.FullPath.indexOf( "/" ) + 1 );
					
					rootFolder = rootFolder.AddFile( projFolder );
					subFolder = href.ToFolder().ToRelative( rootFolder );
				}
				
				var r = rootFolder.FullPath;
				r = r.replace( /\\/g, "/" );
				r = r.replace( /%20/g, " " );
				r = r.replace( /;/g, "%3B" );	// For Safari
				
				mSelf.RootFolder = r;
			}
			else if ( subFolder.FullPath.StartsWith( "AutoMerge", false ) )
			{
				while ( subFolder.FullPath.StartsWith( "AutoMerge", false ) )
				{
					rootFolder = rootFolder.AddFile( "AutoMerge/" );
					subFolder = href.ToFolder().ToRelative( rootFolder );
					
					var projFolder = subFolder.FullPath.substring( 0, subFolder.FullPath.indexOf( "/" ) + 1 );
					
					rootFolder = rootFolder.AddFile( projFolder );
					subFolder = href.ToFolder().ToRelative( rootFolder );
				}
				
				var r = rootFolder.FullPath;
				r = r.replace( /\\/g, "/" );
				r = r.replace( /%20/g, " " );
				r = r.replace( /;/g, "%3B" );	// For Safari
				
				mSelf.RootFolder = r;
			}
			else
			{
				mSelf.RootFolder = FMCGetRootFolder( mSelf.RootFrame.document.location );
			}
		}
		else if ( FMCIsHtmlHelp() )
		{
			mSelf.RootFolder = "/";
		}
		else if ( FMCIsDotNetHelp() )
		{
			var rootFolder	= FMCGetRootFolder( mSelf.BodyFrame.document.location );
			
			mSelf.RootFolder = rootFolder.substring( 0, rootFolder.lastIndexOf( "/", rootFolder.length - 2 ) + 1 );
		}
	}
}

//
//    Helper functions
//

var gImages	= new Array();

function FMCIsWebHelp()
{
	return FMCGetRootFrame() != null;
}

function FMCIsWebHelpAIR()
{
	return document.location.href.StartsWith( "app:/" );
}

function FMCIsHtmlHelp()
{
	var href	= document.location.href;
	
	return href.indexOf( "mk:" ) == 0;
}

function FMCIsDotNetHelp()
{
	return FMCGetRootFrame() == null && !FMCIsHtmlHelp();
}

function FMCIsTopicPopup( win )
{
	return win.parent != win && win.parent.name == "body";
}

var gLiveHelpEnabled	= null;

function FMCIsLiveHelpEnabled()
{
	if ( gLiveHelpEnabled == null )
	{
		var xmlDoc		= CMCXmlParser.GetXmlDoc( MCGlobals.RootFolder + MCGlobals.SubsystemFile, false, null, null );
		
		if ( xmlDoc == null )
		{
			gLiveHelpEnabled = false;
		}
		else
		{
			var projectID	= xmlDoc.documentElement.getAttribute( "LiveHelpOutputId" );
			
			gLiveHelpEnabled = projectID != null;
		}
	}
	
	return gLiveHelpEnabled;
}

function FMCInPreviewMode()
{
	return MCGlobals.InPreviewMode;
}

var gSkinPreviewMode	= null;

function FMCIsSkinPreviewMode()
{
	if ( gSkinPreviewMode == null )
	{
		var xmlDoc		= CMCXmlParser.GetXmlDoc( MCGlobals.RootFolder + MCGlobals.SubsystemFile, false, null, null );
		
		if ( xmlDoc == null )
		{
			gSkinPreviewMode = false;
		}
		else
		{
			gSkinPreviewMode = FMCGetAttributeBool( xmlDoc.documentElement, "SkinPreviewMode", false );
		}
	}
	
	return gSkinPreviewMode;
}

function FMCIsIE55()
{
	return navigator.appVersion.indexOf( "MSIE 5.5" ) != -1;
}

function FMCIsSafari()
{
	return typeof( document.clientHeight ) != "undefined";
}

function FMCGetSkinFolder()
{
	var skinFolder	= null;
	
	if ( MCGlobals.RootFrame != null )
	{
		skinFolder = MCGlobals.RootFrame.gSkinFolder;
	}
	else
	{
		skinFolder = MCGlobals.SkinFolder;
	}
	
	return skinFolder;
}

function FMCGetSkinFolderAbsolute()
{
	var skinFolder	= null;
	
	if ( MCGlobals.RootFrame != null )
	{
		skinFolder = MCGlobals.RootFrame.MCGlobals.RootFolder + MCGlobals.RootFrame.gSkinFolder;
	}
	else
	{
		skinFolder = MCGlobals.RootFolder + MCGlobals.SkinFolder;
	}
	
	return skinFolder;
}

function FMCGetHref( currLocation )
{
	var href	= currLocation.protocol + (!FMCIsHtmlHelp() ? "//" : "") + currLocation.host + currLocation.pathname;

	href = FMCEscapeHref( href );

	return href;
}

function FMCEscapeHref( href )
{
	var newHref	= href.replace( /\\/g, "/" );
	newHref = newHref.replace( /%20/g, " " );
	newHref = newHref.replace( /;/g, "%3B" );	// For Safari

	return newHref;
}

function FMCGetRootFolder( currLocation )
{
	var href		= FMCGetHref( currLocation );
	var rootFolder	= href.substring( 0, href.lastIndexOf( "/" ) + 1 );

	return rootFolder;
}

function FMCGetPathnameFolder( currLocation )
{
	var pathname	= currLocation.pathname;

	// This is for when viewing over a network. IE needs the path to be like this.

	if ( currLocation.protocol.StartsWith( "file" ) )
	{
		if ( !String.IsNullOrEmpty( currLocation.host ) )
		{
			pathname = "/" + currLocation.host + currLocation.pathname;
		}
	}

	//

	pathname = pathname.replace( /\\/g, "/" );
	//pathname = pathname.replace( /%20/g, " " );
	pathname = pathname.replace( /;/g, "%3B" );	// For Safari
	pathname = pathname.substring( 0, pathname.lastIndexOf( "/" ) + 1 );

	return pathname;
}

function FMCGetRootFrame()
{
	var currWindow	= window;
	
	while ( currWindow )
	{
		if ( currWindow.gRootFolder )
		{
			break;
		}
		else if ( currWindow == top )
		{
			currWindow = null;
			
			break;
		}
		
		currWindow = currWindow.parent;
	}
	
	return currWindow;
}

function FMCPreloadImage( imgPath )
{
	if ( imgPath == null )
	{
		return;
	}
	
	if ( imgPath.StartsWith( "url", false ) && imgPath.EndsWith( ")", false ) )
	{
		imgPath = FMCStripCssUrl( imgPath );
	}
	
	var index	= gImages.length;
	
    gImages[index] = new Image();
    gImages[index].src = imgPath;
}

function FMCTrim( str )
{
    return FMCLTrim( FMCRTrim( str ) );
}

function FMCLTrim( str )
{
    for ( var i = 0; i < str.length && str.charAt( i ) == " "; i++ );
    
    return str.substring( i, str.length );
}

function FMCRTrim( str )
{
    for ( var i = str.length - 1; i >= 0 && str.charAt( i ) == " "; i-- );
    
    return str.substring( 0, i + 1 );
}

function FMCContainsClassRoot( className )
{
    var ret = null;
    
    for ( var i = 1; i < arguments.length; i++ )
    {
        var classRoot = arguments[i];
        
        if ( className && (className == classRoot || className.indexOf( classRoot + "_" ) == 0) )
        {
            ret = classRoot;
            
            break;
        }
    }
    
    return ret;
}

function FMCGetChildNodeByTagName( node, tagName, index )
{
    var foundNode   = null;
    var numFound    = -1;
    
    for ( var currNode = node.firstChild; currNode != null; currNode = currNode.nextSibling )
    {
        if ( currNode.nodeName == tagName )
        {
            numFound++;
            
            if ( numFound == index )
            {
                foundNode = currNode;
                
                break;
            }
        }
    }
    
    return foundNode;
}

function FMCGetChildNodesByTagName( node, tagName )
{
    var nodes   = new Array();
    
    for ( var i = 0; i < node.childNodes.length; i++ )
    {
        if ( node.childNodes[i].nodeName == tagName )
        {
            nodes[nodes.length] = node.childNodes[i];
        }
    }
    
    return nodes;
}

function FMCGetChildNodeByAttribute( node, attributeName, attributeValue )
{
	var foundNode   = null;

	for ( var currNode = node.firstChild; currNode != null; currNode = currNode.nextSibling )
	{
		if ( currNode.getAttribute( attributeName ) == attributeValue )
		{
			foundNode = currNode;

			break;
		}
	}

	return foundNode;
}

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

function FMCStringToBool( stringValue )
{
	var boolValue		= false;
	var stringValLower	= stringValue.toLowerCase();

	boolValue = stringValLower == "true" || stringValLower == "1" || stringValLower == "yes";

	return boolValue;
}

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

function FMCGetAttributeBool( node, attributeName, defaultValue )
{
	var boolValue	= defaultValue;
	var value		= FMCGetAttribute( node, attributeName );
	
	if ( value )
	{
		boolValue = FMCStringToBool( value );
	}
	
	return boolValue;
}

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

function FMCGetAttributeInt( node, attributeName, defaultValue )
{
	var intValue	= defaultValue;
	var value		= FMCGetAttribute( node, attributeName );
	
	if ( value != null )
	{
		intValue = parseInt( value );
	}
	
	return intValue;
}

function FMCGetAttributeStringList( node, attributeName, delimiter )
{
	var list	= null;
	var value	= FMCGetAttribute( node, attributeName );
	
	if ( value != null )
	{
		list = value.split( delimiter );
	}
	
	return list;
}

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

function FMCGetAttribute( node, attribute )
{
    var value   = null;
    
    if ( node.getAttribute( attribute ) != null )
    {
        value = node.getAttribute( attribute );
    }
    else if ( node.getAttribute( attribute.toLowerCase() ) != null )
    {
        value = node.getAttribute( attribute.toLowerCase() );
    }
    else
    {
		var namespaceIndex	= attribute.indexOf( ":" );
		
		if ( namespaceIndex != -1 )
		{
			value = node.getAttribute( attribute.substring( namespaceIndex + 1, attribute.length ) );
		}
    }
    
    if ( typeof( value ) == "string" && value == "" )
    {
		value = null;
    }
    
    return value;
}

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

function FMCGetMCAttribute( node, attribute )
{
	var value	= null;
	
    if ( node.getAttribute( attribute ) != null )
    {
        value = node.getAttribute( attribute );
    }
    else if ( node.getAttribute( attribute.substring( "MadCap:".length, attribute.length ) ) )
    {
        value = node.getAttribute( attribute.substring( "MadCap:".length, attribute.length ) );
    }
    
    return value;
}

function FMCRemoveMCAttribute( node, attribute )
{
	var value	= null;
	
    if ( node.getAttribute( attribute ) != null )
    {
        value = node.removeAttribute( attribute );
    }
    else if ( node.getAttribute( attribute.substring( "MadCap:".length, attribute.length ) ) )
    {
        value = node.removeAttribute( attribute.substring( "MadCap:".length, attribute.length ) );
    }
    
    return value;
}

function FMCGetClientWidth( winNode, includeScrollbars )
{
    var clientWidth = null;
    
    if ( typeof( winNode.innerWidth ) != "undefined" )
    {
        clientWidth = winNode.innerWidth;
        
        if ( !includeScrollbars && FMCGetScrollHeight( winNode ) > winNode.innerHeight )
        {
            clientWidth -= 19;
        }
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        clientWidth = winNode.document.body.clientWidth;
    }
    else if ( winNode.document.documentElement )
    {
        clientWidth = winNode.document.documentElement.clientWidth;
    }
    
    return clientWidth;
}

function FMCGetClientHeight( winNode, includeScrollbars )
{
    var clientHeight    = null;
    
    if ( typeof( winNode.innerHeight ) != "undefined" )
    {
        clientHeight = winNode.innerHeight;
        
        if ( !includeScrollbars && FMCGetScrollWidth( winNode ) > winNode.innerWidth )
        {
            clientHeight -= 19;
        }
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        clientHeight = winNode.document.body.clientHeight;
    }
    else if ( winNode.document.documentElement )
    {
        clientHeight = winNode.document.documentElement.clientHeight;
    }
    
    return clientHeight;
}

function FMCGetClientCenter( winNode )
{
	var centerX	= FMCGetScrollLeft( winNode ) + (FMCGetClientWidth( winNode, false ) / 2);
	var centerY	= FMCGetScrollTop( winNode ) + (FMCGetClientHeight( winNode, false ) / 2);
	
	return [centerX, centerY];
}

function FMCGetScrollHeight( winNode )
{
    var scrollHeight    = null;
    
    if ( winNode.document.scrollHeight )
    {
        scrollHeight = winNode.document.scrollHeight;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        scrollHeight = winNode.document.body.scrollHeight;
    }
    else if ( winNode.document.documentElement )
    {
        scrollHeight = winNode.document.documentElement.scrollHeight;
    }
    
    return scrollHeight;
}

function FMCGetScrollWidth( winNode )
{
    var scrollWidth = null;
    
    if ( winNode.document.scrollWidth )
    {
        scrollWidth = winNode.document.scrollWidth;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        scrollWidth = winNode.document.body.scrollWidth;
    }
    else if ( winNode.document.documentElement )
    {
        scrollWidth = winNode.document.documentElement.scrollWidth;
    }
    
    return scrollWidth;
}

function FMCGetScrollTop( winNode )
{
    var scrollTop   = null;
    
    if ( FMCIsSafari() )
    {
        scrollTop = winNode.document.body.scrollTop;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        scrollTop = winNode.document.body.scrollTop;
    }
    else if ( winNode.document.documentElement )
    {
        scrollTop = winNode.document.documentElement.scrollTop;
    }
    
    return scrollTop;
}

function FMCSetScrollTop( winNode, value )
{
    if ( FMCIsSafari() )
    {
        winNode.document.body.scrollTop = value;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        winNode.document.body.scrollTop = value;
    }
    else if ( winNode.document.documentElement )
    {
        winNode.document.documentElement.scrollTop = value;
    }
}

function FMCGetScrollLeft( winNode )
{
    var scrollLeft  = null;
    
    if ( FMCIsSafari() )
    {
        scrollLeft = winNode.document.body.scrollLeft;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        scrollLeft = winNode.document.body.scrollLeft;
    }
    else if ( winNode.document.documentElement )
    {
        scrollLeft = winNode.document.documentElement.scrollLeft;
    }
    
    return scrollLeft;
}

function FMCSetScrollLeft( winNode, value )
{
    if ( FMCIsSafari() )
    {
        winNode.document.body.scrollLeft = value;
    }
    else if ( FMCIsQuirksMode( winNode ) )
    {
        winNode.document.body.scrollLeft = value;
    }
    else if ( winNode.document.documentElement )
    {
        winNode.document.documentElement.scrollLeft = value;
    }
}

function FMCGetClientX( winNode, e )
{
    var clientX;
    
    if ( typeof( e.pageX ) != "undefined" )
    {
        clientX = e.pageX - FMCGetScrollLeft( winNode );
    }
    else if ( typeof( e.clientX ) != "undefined" )
    {
        clientX = e.clientX;
    }
    
    return clientX;
}

function FMCGetClientY( winNode, e )
{
    var clientY;
    
    if ( typeof( e.pageY ) != "undefined" )
    {
        clientY = e.pageY - FMCGetScrollTop( winNode );
    }
    else if ( typeof( e.clientY ) != "undefined" )
    {
        clientY = e.clientY;
    }
    
    return clientY;
}

function FMCGetPageX( winNode, e )
{
    var pageX;
    
    if ( typeof( e.pageX ) != "undefined" )
    {
        pageX = e.pageX;
    }
    else if ( typeof( e.clientX ) != "undefined" )
    {
        pageX = e.clientX + FMCGetScrollLeft( winNode );
    }
    
    return pageX;
}

function FMCGetPageY( winNode, e )
{
    var pageY;
    
    if ( typeof( e.pageY ) != "undefined" )
    {
        pageY = e.pageY;
    }
    else if ( typeof( e.clientY ) != "undefined" )
    {
        pageY = e.clientY + FMCGetScrollTop( winNode );
    }
    
    return pageY;
}

function FMCGetMouseXRelativeTo( winNode, e, el )
{
	var mouseX	= FMCGetPageX( winNode, e, el );
	var elX		= FMCGetPosition( el )[1];
	var x		= mouseX - elX;

	return x;
}

function FMCGetMouseYRelativeTo( winNode, e, el )
{
	var mouseY	= FMCGetPageY( winNode, e, el );
	var elY		= FMCGetPosition( el )[0];
	var y		= mouseY - elY;

	return y;
}

function FMCGetPosition( node )
{
	var topPos	= 0;
	var leftPos	= 0;
	
	if ( node.offsetParent )
	{
		topPos = node.offsetTop;
		leftPos = node.offsetLeft;
		
		while ( node = node.offsetParent )
		{
			topPos += node.offsetTop;
			leftPos += node.offsetLeft;
		}
	}
	
	return [topPos, leftPos];
}

function FMCScrollToVisible( win, node )
{
	var offset			= 0;
    
    if ( typeof( window.innerWidth ) != "undefined" && !FMCIsSafari() )
    {
		offset = 19;
    }
    
    var scrollTop		= FMCGetScrollTop( win );
    var scrollBottom	= scrollTop + FMCGetClientHeight( win, false ) - offset;
    var scrollLeft		= FMCGetScrollLeft( win );
    var scrollRight		= scrollLeft + FMCGetClientWidth( win, false ) - offset;
    
    var nodePos			= FMCGetPosition( node );
    var nodeTop			= nodePos[0];
    var nodeLeft		= parseInt( node.style.textIndent ) + nodePos[1];
    var nodeHeight		= node.offsetHeight;
    var nodeWidth		= node.getElementsByTagName( "a" )[0].offsetWidth;
    
    if ( nodeTop < scrollTop )
    {
        FMCSetScrollTop( win, nodeTop );
    }
    else if ( nodeTop + nodeHeight > scrollBottom )
    {
        FMCSetScrollTop( win, Math.min( nodeTop, nodeTop + nodeHeight - FMCGetClientHeight( win, false ) + offset ) );
    }
    
    if ( nodeLeft < scrollLeft )
    {
        FMCSetScrollLeft( win, nodeLeft );
    }
    else if ( nodeLeft + nodeWidth > scrollRight )
    {
		FMCSetScrollLeft( win, Math.min( nodeLeft, nodeLeft + nodeWidth - FMCGetClientWidth( win, false ) + offset ) );
    }
}

function FMCIsQuirksMode( winNode )
{
	return FMCIsIE55() || (winNode.document.compatMode && winNode.document.compatMode == "BackCompat");
}

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

function FMCGetComputedStyle( node, style )
{
    var value   = null;
    
    if ( node.currentStyle )
    {
        value = node.currentStyle[style];
    }
    else if ( document.defaultView && document.defaultView.getComputedStyle )
    {
		var computedStyle	= document.defaultView.getComputedStyle( node, null );
		
		if ( computedStyle )
		{
			value = computedStyle[style];
		}
    }
    
    return value;
}

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

function FMCConvertToPx( doc, str, dimension, defaultValue )
{
    if ( !str || str.charAt( 0 ) == "-" )
    {
        return defaultValue;
    }
    
    if ( str.charAt( str.length - 1 ) == "\%" )
    {
        switch (dimension)
        {
            case "Width":
                return parseInt( str ) * screen.width / 100;
                
                break;
            case "Height":
                return parseInt( str ) * screen.height / 100;
                
                break;
        }
    }
    else
    {
		if ( parseInt( str ).toString() == str )
		{
			str += "px";
		}
    }
    
    try
    {
        var div	= doc.createElement( "div" );
    }
    catch ( err )
    {
        return defaultValue;
    }
    
    doc.body.appendChild( div );
    
    var value	= defaultValue;
    
    try
    {
        div.style.width = str;
        
        if ( div.currentStyle )
		{
			value = div.offsetWidth;
		}
		else if ( document.defaultView && document.defaultView.getComputedStyle )
		{
			value = parseInt( FMCGetComputedStyle( div, "width" ) );
		}
    }
    catch ( err )
    {
    }
    
    doc.body.removeChild( div );
    
    return value;
}

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

function FMCGetControl( el )
{
	var value	= null;
	
	if ( el.type == "checkbox" )
	{
		value = el.checked;
	}
	else
	{
		value = el.value;
	}
	
	return value;
}

function FMCGetOpacity( el )
{
	var opacity	= -1;
	
	if ( el.filters )
	{
		opacity = parseInt( el.style.filter.substring( 17, el.style.filter.length - 2 ) );
	}
	else if ( el.style.MozOpacity != null )
	{
		opacity = parseFloat( el.style.MozOpacity ) * 100;
	}
	
	return opacity;
}

function FMCSetOpacity( el, opacityPercent )
{
	if ( el.filters )
	{
		// IE bug: If a text input field is contained within an element that has an opacity set and it contains too much text to fit inside it,
		// using the keyboard to move the cursor to scroll the text will result in the text not "refreshing" in the text input field.
		// The workaround is to set the opacity to "" in IE when it becomes 100. That way, the cursor issue will be fixed inside our dialogs
		// which fade in to 100% opacity when they're opened.
		
		if ( opacityPercent == 100 )
		{
			el.style.filter = "";
		}
		else
		{
			el.style.filter = "alpha( opacity = " + opacityPercent + " )";
		}
	}
	else if ( el.style.MozOpacity != null )
	{
		el.style.MozOpacity = opacityPercent / 100;
	}
}

function FMCToggleDisplay( el )
{
	if ( el.style.display == "none" )
	{
		el.style.display = "";
	}
	else
	{
		el.style.display = "none";
	}
}

function FMCIsChildNode( childNode, parentNode )
{
	var	doc	= parentNode.ownerDocument;
	
	if ( childNode == null )
	{
		return null;
	}
	
	for ( var currNode = childNode; ; currNode = currNode.parentNode )
	{
		if ( currNode == parentNode )
		{
			return true;
		}
		
		if ( currNode == doc.body )
		{
			return false;
		}
	}
}

function FMCStripCssUrl( url )
{
	if ( !url )
	{
		return null;
	}
	
	var regex	= /url\(\s*(['\"]?)([^'\"\s]*)\1\s*\)/;
	var match	= regex.exec( url );
	
	if ( match )
	{
		return match[2];
	}
	
	return null;
}

function FMCCreateCssUrl( path )
{
	return "url(\"" + path + "\")";
}

function FMCGetPropertyValue( propertyNode, defaultValue )
{
	var propValue	= defaultValue;
	var valueNode	= propertyNode.firstChild;
	
	if ( valueNode )
	{
		propValue = valueNode.nodeValue;
	}
	
	return propValue;
}

function FMCParseInt( str, defaultValue )
{
	var num	= parseInt( str );

	if ( num.toString() == "NaN" )
	{
		num = defaultValue;
	}
	
	return num;
}

function FMCConvertBorderToPx( doc, value )
{
	var newValue	= "";
	var valueParts	= value.split( " " );

	for ( var i = 0; i < valueParts.length; i++ )
	{
		var currPart	= valueParts[i];
		
		if ( i == 1 )
		{
			currPart = FMCConvertToPx( doc, currPart, null, currPart );
			
			if ( parseInt( currPart ).toString() == currPart )
			{
				currPart += "px";
			}
		}

		if ( !String.IsNullOrEmpty( currPart ) )
		{
			newValue += (((i > 0) ? " " : "") + currPart);
		}
	}
	
	return newValue;
}

function FMCUnhide( win, node )
{
    for ( var currNode = node.parentNode; currNode.nodeName != "BODY"; currNode = currNode.parentNode )
    {
        if ( currNode.style.display == "none" )
        {
            var classRoot   = FMCContainsClassRoot( currNode.className, "MCExpandingBody", "MCDropDownBody", "MCTextPopupBody" );
            
            if ( classRoot == "MCExpandingBody" )
            {
                win.FMCExpand( currNode.parentNode.getElementsByTagName("a")[0] );
            }
            else if ( classRoot == "MCDropDownBody" )
            {
                var dropDownBodyID  = currNode.id.substring( "MCDropDownBody".length + 1, currNode.id.length );
                var aNodes          = currNode.parentNode.getElementsByTagName( "a" );
                
                for ( var i = 0; i < aNodes.length; i++ )
                {
                    var aNode   = aNodes[i];
                    
                    if ( aNode.id.substring( "MCDropDownHotSpot".length + 1, aNode.id.length ) == dropDownBodyID )
                    {
                        win.FMCDropDown( aNode );
                    }
                }
            }
            else if ( FMCGetMCAttribute( currNode, "MadCap:targetName" ) )
            {
                var targetName      = FMCGetMCAttribute( currNode, "MadCap:targetName" );
                var togglerNodes    = FMCGetElementsByClassRoot( win.document.body, "MCToggler" );
                
                for ( var i = 0; i < togglerNodes.length; i++ )
                {
                    var targets = FMCGetMCAttribute( togglerNodes[i], "MadCap:targets" ).split( ";" );
                    var found   = false;
                    
                    for ( var j = 0; j < targets.length; j++ )
                    {
                        if ( targets[j] == targetName )
                        {
                            found = true;
                            
                            break;
                        }
                    }
                    
                    if ( !found )
                    {
                        continue;
                    }
                    
                    win.FMCToggler( togglerNodes[i] );
                    
                    break;
                }
            }
            else if ( classRoot == "MCTextPopupBody" )
            {
                continue;
            }
            else if ( currNode.className == "MCWebHelpFramesetLink" )
            {
                continue;
            }
            else
            {
                currNode.style.display = "";
            }
        }
    }
}

function StartLoading( win, parentElement, loadingLabel, loadingAltText, fadeElement )
{
	if ( !win.MCLoadingCount )
	{
		win.MCLoadingCount = 0;
	}
	
	win.MCLoadingCount++;
	
	if ( win.MCLoadingCount > 1 )
	{
		return;
	}
	
	//
	
	if ( fadeElement )
	{
		// IE bug: This causes the tab outline not to show and also causes the TOC entry fonts to look bold.
		//	if ( fadeElement.filters )
		//	{
		//		fadeElement.style.filter = "alpha( opacity = 10 )";
		//	}
		/*else*/ if ( fadeElement.style.MozOpacity != null )
		{
			fadeElement.style.MozOpacity = "0.1";
		}
	}

	var span		= win.document.createElement( "span" );
	var img			= win.document.createElement( "img" );
	var midPointX	= FMCGetScrollLeft( win ) + FMCGetClientWidth( win, false ) / 2;
	var spacing		= 3;

	parentElement.appendChild( span );

	span.id = "LoadingText";
	span.appendChild( win.document.createTextNode( loadingLabel ) );
	span.style.fontFamily = "Tahoma, Sans-Serif";
	span.style.fontSize = "9px";
	span.style.fontWeight = "bold";
	span.style.position = "absolute";
	span.style.left = (midPointX - (span.offsetWidth / 2)) + "px";

	var rootFrame	= FMCGetRootFrame();
	
	img.id = "LoadingImage";
	img.src = rootFrame.gRootFolder + MCGlobals.SkinTemplateFolder + "Images/Loading.gif";
	img.alt = loadingAltText;
	img.style.width = "70px";
	img.style.height = "13px";
	img.style.position = "absolute";
	img.style.left = (midPointX - (70/2)) + "px";

	var totalHeight	= span.offsetHeight + spacing + parseInt( img.style.height );
	var spanTop		= (FMCGetScrollTop( win ) + (FMCGetClientHeight( win, false ) - totalHeight)) / 2;

	span.style.top = spanTop + "px";
	img.style.top = spanTop + span.offsetHeight + spacing + "px";

	parentElement.appendChild( img );
}

function EndLoading( win, fadeElement )
{
	win.MCLoadingCount--;
	
	if ( win.MCLoadingCount > 0 )
	{
		return;
	}
	
	//
	
	var span	= win.document.getElementById( "LoadingText" );
	var img		= win.document.getElementById( "LoadingImage" );

	span.parentNode.removeChild( span );
	img.parentNode.removeChild( img );

	if ( fadeElement )
	{
		// IE bug: This causes the tab outline not to show and also causes the TOC entry fonts to look bold.
		//	if ( fadeElement.filters )
		//	{
		//		fadeElement.style.filter = "alpha( opacity = 100 )";
		//	}
		/*else*/ if ( fadeElement.style.MozOpacity != null )
		{
			fadeElement.style.MozOpacity = "1.0";
		}
	}
}

var MCEventType	= new Object();

MCEventType.OnLoad	= 0;
MCEventType.OnInit	= 1;
MCEventType.OnReady	= 2;

function FMCRegisterCallback( frameName, eventType, CallbackFunc, callbackArgs )
{
	function FMCCheckMCGlobalsInitialized()
	{
		if ( MCGlobals.Initialized )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckMCGlobalsInitialized, 100 );
		}
	}

	function FMCCheckRootReady()
	{
		if ( MCGlobals.RootFrame.gReady )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckRootReady, 100 );
		}
	}

	function FMCCheckRootLoaded()
	{
		if ( MCGlobals.RootFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckRootLoaded, 100 );
		}
	}

	function FMCCheckTOCInitialized()
	{
		if ( MCGlobals.NavigationFrame.frames["toc"].gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckTOCInitialized, 100 );
		}
	}

	function FMCCheckSearchInitialized()
	{
		if ( MCGlobals.NavigationFrame.frames["search"].gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckSearchInitialized, 100 );
		}
	}

	function FMCCheckTopicCommentsLoaded()
	{
		if ( MCGlobals.TopicCommentsFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckTopicCommentsLoaded, 100 );
		}
	}

	function FMCCheckTopicCommentsInitialized()
	{
		if ( MCGlobals.TopicCommentsFrame.gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckTopicCommentsInitialized, 100 );
		}
	}
	
	function FMCCheckRecentCommentsLoaded()
	{
		if ( MCGlobals.RecentCommentsFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckRecentCommentsLoaded, 100 );
		}
	}

	function FMCCheckRecentCommentsInitialized()
	{
		if ( MCGlobals.RecentCommentsFrame.gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckRecentCommentsInitialized, 100 );
		}
	}

	function FMCCheckBodyCommentsLoaded()
	{
		if ( MCGlobals.BodyCommentsFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckBodyCommentsLoaded, 100 );
		}
	}

	function FMCCheckBodyCommentsInitialized()
	{
		if ( MCGlobals.BodyCommentsFrame.gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckBodyCommentsInitialized, 100 );
		}
	}

	function FMCCheckToolbarInitialized()
	{
		if ( MCGlobals.ToolbarFrame.gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckToolbarInitialized, 100 );
		}
	}

	function FMCCheckNavigationReady()
	{
		if ( MCGlobals.NavigationFrame.gReady )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckNavigationReady, 100 );
		}
	}

	function FMCCheckNavigationLoaded()
	{
		if ( MCGlobals.NavigationFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckNavigationLoaded, 100 );
		}
	}

	function FMCCheckBodyReady()
	{
		if ( typeof( MCGlobals.BodyFrame.gReady ) == "undefined" || MCGlobals.BodyFrame.gReady )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckBodyReady, 100 );
		}
	}

	function FMCCheckBodyLoaded()
	{
		if ( MCGlobals.BodyFrame.gLoaded )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckBodyLoaded, 100 );
		}
	}

	function FMCCheckPersistenceInitialized()
	{
		if ( MCGlobals.PersistenceFrame.gInit )
		{
			CallbackFunc( callbackArgs );
		}
		else
		{
			setTimeout( FMCCheckPersistenceInitialized, 100 );
		}
	}
	
	var func	= null;
	
	if ( frameName == "TOC" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckTOCLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckTOCInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckTOCReady; }
	}
	else if ( frameName == "Toolbar" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckToolbarLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckToolbarInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckToolbarReady; }
	}
	else if ( frameName == "BodyComments" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckBodyCommentsLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckBodyCommentsInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckBodyCommentsReady; }
	}
	else if ( frameName == "TopicComments" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckTopicCommentsLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckTopicCommentsInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckTopicCommentsReady; }
	}
	else if ( frameName == "RecentComments" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckRecentCommentsLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckRecentCommentsInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckRecentCommentsReady; }
	}
	else if ( frameName == "Persistence" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckPersistenceLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckPersistenceInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckPersistenceReady; }
	}
	else if ( frameName == "Search" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckSearchLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckSearchInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckSearchReady; }
	}
	else if ( frameName == "MCGlobals" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckMCGlobalsLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckMCGlobalsInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckMCGlobalsReady; }
	}
	else if ( frameName == "Navigation" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckNavigationLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckNavigationInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckNavigationReady; }
	}
	else if ( frameName == "Body" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckBodyLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckBodyInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckBodyReady; }
	}
	else if ( frameName == "Root" )
	{
		if ( eventType == MCEventType.OnLoad ) { func = FMCCheckRootLoaded; }
		else if ( eventType == MCEventType.OnInit ) { func = FMCCheckRootInitialized; }
		else if ( eventType == MCEventType.OnReady ) { func = FMCCheckRootReady; }
	}
	
	window.setTimeout( func, 100 );
}

function FMCSortStringArray( stringArray )
{
	stringArray.sort( FMCCompareStrings );
}

function FMCCompareStrings( a, b )
{
	var ret;

	if ( a.toLowerCase() < b.toLowerCase() )
	{
		ret = -1;
	}
	else if ( a.toLowerCase() == b.toLowerCase() )
	{
		ret = 0;
	}
	else if ( a.toLowerCase() > b.toLowerCase() )
	{
		ret = 1;
	}

	return ret;
}

function FMCSetCookie( name, value, days )
{
	if ( window.name != "bridge" )
	{
		if ( window != MCGlobals.NavigationFrame )
		{
			MCGlobals.NavigationFrame.FMCSetCookie( name, value, days );
			
			return;
		}
	}
	
	value = encodeURI( value );
	
	var expires = null;
	
	if ( days )
	{
		var date	= new Date();
	    
		date.setTime( date.getTime() + (1000 * 60 * 60 * 24 * days) );
	    
		expires = "; expires=" + date.toGMTString();
	}
	else
	{
		expires = "";
	}

//	var rootFrame	= FMCGetRootFrame();
//	var navFrame	= rootFrame.frames["navigation"];
//	var path		= FMCGetPathnameFolder( navFrame.document.location );

//	navFrame.document.cookie = name + "=" + value + expires + ";" + " path=" + path + ";";

	var cookieString = name + "=" + value + expires + ";";
	
	document.cookie = cookieString;
}

function FMCReadCookie( name )
{
	if ( window.name != "bridge" )
	{
		if ( window != MCGlobals.NavigationFrame )
		{
			return MCGlobals.NavigationFrame.FMCReadCookie( name );
		}
	}
	
	var value		= null;
	var nameEq		= name + "=";
//	var rootFrame	= FMCGetRootFrame();
//	var navFrame	= rootFrame.frames["navigation"];
//	var cookies		= navFrame.document.cookie.split( ";" );
	var cookies		= document.cookie.split( ";" );

	for ( var i = 0; i < cookies.length; i++ )
	{
		var cookie	= cookies[i];
	    
		cookie = FMCTrim( cookie );
	    
		if ( cookie.indexOf( nameEq ) == 0 )
		{
			value = cookie.substring( nameEq.length, cookie.length );
			value = decodeURI( value );
			
			break;
		}
	}

	return value;
}

function FMCRemoveCookie( name )
{
	FMCSetCookie( name, "", -1 );
}

function FMCLoadUserData( name )
{
	if ( FMCIsHtmlHelp() )
	{
		var persistFrame	= MCGlobals.PersistenceFrame;
		var persistDiv		= persistFrame.document.getElementById( "Persist" );
		
		persistDiv.load( "MCXMLStore" );
		
		var value	= persistDiv.getAttribute( name );
		
		return value;
	}
	else
	{
		return FMCReadCookie( name );
	}
}

function FMCSaveUserData( name, value )
{
	if ( FMCIsHtmlHelp() )
	{
		var persistFrame	= MCGlobals.PersistenceFrame;
		var persistDiv		= persistFrame.document.getElementById( "Persist" );
		
		persistDiv.setAttribute( name, value );
		persistDiv.save( "MCXMLStore" );
	}
	else
	{
		FMCSetCookie( name, value, 36500 );
	}
}

function FMCRemoveUserData( name )
{
	if ( FMCIsHtmlHelp() )
	{
		var persistFrame	= MCGlobals.PersistenceFrame;
		var persistDiv		= persistFrame.document.getElementById( "Persist" );
		
		persistDiv.removeAttribute( name );
		persistDiv.save( "MCXMLStore" );
	}
	else
	{
		FMCRemoveCookie( name );
	}
}

function FMCInsertOpacitySheet( winNode, color )
{
	var div		= winNode.document.createElement( "div" );
	var style	= div.style;
	
	div.id = "MCOpacitySheet";
	style.position = "absolute";
	style.top = FMCGetScrollTop( winNode ) + "px";
	style.left = FMCGetScrollLeft( winNode ) + "px";
	style.width = FMCGetClientWidth( winNode, false ) + "px";
	style.height = FMCGetClientHeight( winNode, false ) + "px";
	style.backgroundColor = color;
	style.zIndex = "100";
	
	winNode.document.body.appendChild( div );
	
	FMCSetOpacity( div, 75 );
}

function FMCRemoveOpacitySheet( winNode )
{
	var div	= winNode.document.getElementById( "MCOpacitySheet" );
	
	if ( !div )
	{
		return;
	}
	
	div.parentNode.removeChild( div );
}

function FMCSetupButtonFromStylesheet( tr, styleName, styleClassName, defaultOutPath, defaultOverPath, defaultSelectedPath, defaultWidth, defaultHeight, defaultTooltip, defaultLabel, OnClickHandler )
{
	var td					= document.createElement( "td" );
	var outImagePath		= CMCFlareStylesheet.LookupValue( styleName, styleClassName, "Icon", null );
	var overImagePath		= CMCFlareStylesheet.LookupValue( styleName, styleClassName, "HoverIcon", null );
	var selectedImagePath	= CMCFlareStylesheet.LookupValue( styleName, styleClassName, "PressedIcon", null );
	
	if ( outImagePath == null )
	{
		outImagePath = defaultOutPath;
	}
	else
	{
		outImagePath = FMCStripCssUrl( outImagePath );
		outImagePath = FMCGetSkinFolderAbsolute() + outImagePath;
	}
	
	if ( overImagePath == null )
	{
		overImagePath = defaultOverPath;
	}
	else
	{
		overImagePath = FMCStripCssUrl( overImagePath );
		overImagePath = FMCGetSkinFolderAbsolute() + overImagePath;
	}
	
	if ( selectedImagePath == null )
	{
		selectedImagePath = defaultSelectedPath;
	}
	else
	{
		selectedImagePath = FMCStripCssUrl( selectedImagePath );
		selectedImagePath = FMCGetSkinFolderAbsolute() + selectedImagePath;
	}

	tr.appendChild( td );
	
	var title	= CMCFlareStylesheet.LookupValue( styleName, styleClassName, "Tooltip", defaultTooltip );
	var label	= CMCFlareStylesheet.LookupValue( styleName, styleClassName, "Label", defaultLabel );
	var width	= CMCFlareStylesheet.GetResourceProperty( outImagePath, "Width", defaultWidth );
	var height	= CMCFlareStylesheet.GetResourceProperty( outImagePath, "Height", defaultHeight );
	
	MakeButton( td, title, outImagePath, overImagePath, selectedImagePath, width, height, label );
	td.firstChild.onclick = OnClickHandler;
}

function FMCEscapeRegEx( str )
{
	return str.replace( /([*^$+?.()[\]{}|\\])/g, "\\$1" );
}

//
//    End helper functions
//

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

//
//    Class CMCXmlParser
//

function CMCXmlParser( args, LoadFunc )
{
	// Private member variables and functions
	
	var mSelf		= this;
    this.mXmlDoc	= null;
    this.mXmlHttp	= null;
    this.mArgs		= args;
    this.mLoadFunc	= LoadFunc;
    
    this.OnreadystatechangeLocal	= function()
	{
		if ( mSelf.mXmlDoc.readyState == 4 )
		{
			mSelf.mLoadFunc( mSelf.mXmlDoc, mSelf.mArgs );
		}
	};
	
	this.OnreadystatechangeRemote	= function()
	{
		if ( mSelf.mXmlHttp.readyState == 4 )
		{
			mSelf.mLoadFunc( mSelf.mXmlHttp.responseXML, mSelf.mArgs );
		}
	};
}

CMCXmlParser.prototype.LoadLocal	= function( xmlFile, async )
{
	if ( window.ActiveXObject )
    {
        this.mXmlDoc = new ActiveXObject( "Microsoft.XMLDOM" );
        this.mXmlDoc.async = async;
        
        if ( this.mLoadFunc )
        {
			this.mXmlDoc.onreadystatechange = this.OnreadystatechangeLocal;
        }
        
        try
        {
            if ( !this.mXmlDoc.load( xmlFile ) )
            {
                this.mXmlDoc = null;
            }
        }
        catch ( err )
        {
			this.mXmlDoc = null;
        }
    }
    else if ( window.XMLHttpRequest )
    {
        this.LoadRemote( xmlFile, async ); // window.XMLHttpRequest also works on local files
    }

    return this.mXmlDoc;
};

CMCXmlParser.prototype.LoadRemote	= function( xmlFile, async )
{
	if ( window.ActiveXObject )
    {
        this.mXmlHttp = new ActiveXObject( "Msxml2.XMLHTTP" );
    }
    else if ( window.XMLHttpRequest )
    {
        xmlFile = xmlFile.replace( /;/g, "%3B" );   // For Safari
        this.mXmlHttp = new XMLHttpRequest();
    }
    
    if ( this.mLoadFunc )
    {
		this.mXmlHttp.onreadystatechange = this.OnreadystatechangeRemote;
    }
    
    try
    {
		this.mXmlHttp.open( "GET", xmlFile, async );
        this.mXmlHttp.send( null );
        
        if ( !async && (this.mXmlHttp.status == 0 || this.mXmlHttp.status == 200) )
		{
			this.mXmlDoc = this.mXmlHttp.responseXML;
		}
    }
    catch ( err )
    {
		this.mXmlHttp.abort();
    }
    
    return this.mXmlDoc;
};

// Public member functions

CMCXmlParser.prototype.Load	= function( xmlFile, async )
{
	var xmlDoc			= null;
	var protocolType	= document.location.protocol;
	
	if ( protocolType == "file:" || protocolType == "mk:" || protocolType == "app:" )
	{
		xmlDoc = this.LoadLocal( xmlFile, async );
	}
	else if ( protocolType == "http:" || protocolType == "https:" )
	{
		xmlDoc = this.LoadRemote( xmlFile, async );
	}
	
	return xmlDoc;
};

// Static member functions

CMCXmlParser.GetXmlDoc	= function( xmlFile, async, LoadFunc, args )
{
	var xmlParser	= new CMCXmlParser( args, LoadFunc );
    var xmlDoc		= xmlParser.Load( xmlFile, async );
    
    return xmlDoc;
}

CMCXmlParser.LoadXmlString	= function( xmlString )
{
	var xmlDoc	= null;
	
	if ( window.ActiveXObject )
	{
		xmlDoc = new ActiveXObject( "Microsoft.XMLDOM" );
		xmlDoc.async = false;
		xmlDoc.loadXML( xmlString );
	}
	else if ( DOMParser )
	{
		var parser	= new DOMParser();
		
		xmlDoc = parser.parseFromString( xmlString, "text/xml" );
	}
    
    return xmlDoc;
}

CMCXmlParser.CreateXmlDocument	= function( rootTagName )
{
	var rootXml	= "<" + rootTagName + " />";
	var xmlDoc	= CMCXmlParser.LoadXmlString( rootXml );
    
    return xmlDoc;
}

CMCXmlParser.GetOuterXml	= function( xmlDoc )
{
	var xml	= null;
	
	if ( window.ActiveXObject )
	{
		xml = xmlDoc.xml;
	}
	else if ( window.XMLSerializer )
	{
		var serializer  = new XMLSerializer();
		
		xml = serializer.serializeToString( xmlDoc );
	}
	
	return xml;
}

CMCXmlParser.CallWebService	= function( webServiceUrl, async, onCompleteFunc, onCompleteArgs )
{
	var xmlParser	= new CMCXmlParser( onCompleteArgs, onCompleteFunc );
	var xmlDoc		= xmlParser.LoadRemote( webServiceUrl, async );
    
    return xmlDoc;
}

//
//    End class CMCXmlParser
//

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

//
//    Class CMCFlareStylesheet
//

var CMCFlareStylesheet	= new function()
{
	// Private member variables

	var mInitialized			= false;
	var mXmlDoc					= null;
	var mInitializedResources	= false;
	var mResourceMap			= null;
	
	// Private methods
	
	function Init()
	{
		mXmlDoc = CMCXmlParser.GetXmlDoc( FMCGetSkinFolderAbsolute() + "Stylesheet.xml", false, null, null );
		
		mInitialized = true;
	}
	
	function InitializeResources()
    {
		mInitializedResources = true;
		mResourceMap = new CMCDictionary();
		
		var styleDoc		= CMCXmlParser.GetXmlDoc( FMCGetSkinFolderAbsolute() + "Stylesheet.xml", false, null, null );
		var resourcesInfos	= styleDoc.getElementsByTagName( "ResourcesInfo" );

		if ( resourcesInfos.length > 0 )
		{
			var resources	= resourcesInfos[0].getElementsByTagName( "Resource" );

			for ( var i = 0; i < resources.length; i++ )
			{
				var resource	= resources[i];
				var properties	= new CMCDictionary();
				var name		= resource.getAttribute( "Name" );
				
				if ( !name ) { continue; }

				for ( var j = 0; j < resource.attributes.length; j++ )
				{
					var attribute	= resource.attributes[j];
					
					properties.Add( attribute.nodeName.toLowerCase(), attribute.nodeValue.toLowerCase() );
				}

				mResourceMap.Add( name, properties );
			}
		}
    }
	
	// Public methods
	
	this.LookupValue	= function( styleName, styleClassName, propertyName, defaultValue )
	{
		if ( !mInitialized )
		{
			Init();
			
			if ( mXmlDoc == null )
			{
				return defaultValue;
			}
		}
		
		var value				= defaultValue;
		var styleNodes			= mXmlDoc.getElementsByTagName( "Style" );
		var styleNodesLength	= styleNodes.length;
		var styleNode			= null;
		
		for ( var i = 0; i < styleNodesLength; i++ )
		{
			if ( styleNodes[i].getAttribute( "Name" ) == styleName )
			{
				styleNode = styleNodes[i];
				break;
			}
		}
		
		if ( styleNode == null )
		{
			return value;
		}
		
		var styleClassNodes			= styleNode.getElementsByTagName( "StyleClass" );
		var styleClassNodesLength	= styleClassNodes.length;
		var styleClassNode			= null;
		
		for ( var i = 0; i < styleClassNodesLength; i++ )
		{
			if ( styleClassNodes[i].getAttribute( "Name" ) == styleClassName )
			{
				styleClassNode = styleClassNodes[i];
				break;
			}
		}
		
		if ( styleClassNode == null )
		{
			return value;
		}
		
		var propertyNodes		= styleClassNode.getElementsByTagName( "Property" );
		var propertyNodesLength	= propertyNodes.length;
		var propertyNode		= null;
		
		for ( var i = 0; i < propertyNodesLength; i++ )
		{
			if ( propertyNodes[i].getAttribute( "Name" ) == propertyName )
			{
				propertyNode = propertyNodes[i];
				break;
			}
		}
		
		if ( propertyNode == null )
		{
			return value;
		}
		
		value = propertyNode.firstChild.nodeValue;
		value = FMCTrim( value );
		
		return value;
	};
	
	this.GetResourceProperty	= function( name, property, defaultValue )
	{
		if ( !mInitialized )
		{
			Init();
			
			if ( mXmlDoc == null )
			{
				return defaultValue;
			}
		}
		
		if ( !mInitializedResources )
		{
			InitializeResources();
		}
		
		var properties	= mResourceMap.GetItem( name );

		if ( !properties )
		{
			return defaultValue;
		}

		var propValue	= properties.GetItem( property.toLowerCase() );

		if ( !propValue )
		{
			return defaultValue;
		}

		return propValue;
	};
	
	this.SetImageFromStylesheet	= function( img, styleName, styleClassName, propertyName, defaultValue, defaultWidth, defaultHeight )
	{
		var value	= this.LookupValue( styleName, styleClassName, propertyName, null );
		var imgSrc	= null;
		
		if ( value == null )
		{
			value = defaultValue;
			imgSrc = value;
		}
		else
		{
			value = FMCStripCssUrl( value );
			value = decodeURIComponent( value );
			value = escape( value );
			imgSrc = FMCGetSkinFolderAbsolute() + value;
		}
		
		img.src = imgSrc;
		img.style.width = this.GetResourceProperty( value, "Width", defaultWidth ) + "px";
		img.style.height = this.GetResourceProperty( value, "Height", defaultHeight ) + "px";
	};
}

//
//    End class CMCFlareStylesheet
//

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

//
//    String helpers
//

String.IsNullOrEmpty = function( str )
{
	if ( str == null )
	{
		return true;
	}
	
	if ( str.length == 0 )
	{
		return true;
	}
	
	return false;
}

String.prototype.StartsWith = function( str, caseSensitive )
{
	if ( str == null )
	{
		return false;
	}
	
	if ( this.length < str.length )
	{
		return false;
	}
	
	var value1	= this;
	var value2	= str;
	
	if ( !caseSensitive )
	{
		value1 = value1.toLowerCase();
		value2 = value2.toLowerCase();
	}
	
	if ( value1.substring( 0, value2.length ) == value2 )
	{
		return true;
	}
	else
	{
		return false;
	}
}

String.prototype.EndsWith = function( str, caseSensitive )
{
	if ( str == null )
	{
		return false;
	}
	
	if ( this.length < str.length )
	{
		return false;
	}
	
	var value1	= this;
	var value2	= str;
	
	if ( !caseSensitive )
	{
		value1 = value1.toLowerCase();
		value2 = value2.toLowerCase();
	}
	
	if ( value1.substring( value1.length - value2.length ) == value2 )
	{
		return true;
	}
	else
	{
		return false;
	}
}

String.prototype.Contains = function( str, caseSensitive )
{
	var value1	= this;
	var value2	= str;
	
	if ( !caseSensitive )
	{
		value1 = value1.toLowerCase();
		value2 = value2.toLowerCase();
	}
	
	return value1.indexOf( value2 ) != -1;
}

String.prototype.Equals = function( str, caseSensitive )
{
	var value1	= this;
	var value2	= str;
	
	if ( !caseSensitive )
	{
		value1 = value1.toLowerCase();
		value2 = value2.toLowerCase();
	}
	
	return value1 == value2;
}

String.prototype.CountOf = function( str, caseSensitive )
{
	var count	= 0;
	var value1	= this;
	var value2	= str;
	
	if ( !caseSensitive )
	{
		value1 = value1.toLowerCase();
		value2 = value2.toLowerCase();
	}
	
	var lastIndex	= -1;
	
	while ( true )
	{
		lastIndex = this.indexOf( str, lastIndex + 1 );
		
		if ( lastIndex == -1 )
		{
			break;
		}
		
		count++;
	}
	
	return count;
}

String.prototype.Insert = function( startIndex, value )
{
	var newStr = null;
	
	if ( startIndex >= 0 )
	{
		newStr = this.substring( 0, startIndex );
	}
	else
	{
		newStr = this;
	}
	
	newStr += value;
	
	if ( startIndex >= 0 )
	{
		newStr += this.substring( startIndex );
	}
	
	return newStr;
}

//
//    End String helpers
//

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

//
//    Array helpers
//

Array.prototype.Contains = function( item )
{
	for ( var i = 0, length = this.length; i < length; i++ )
	{
		if ( this[i] == item )
		{
			return true;
		}
	}
	
	return false;
}

Array.prototype.Insert = function( item, index )
{
	if ( index < 0 || index > this.length )
	{
		throw "Index out of bounds.";
	}
	
	this.splice( index, 0, item );
}

//
//    End Array helpers
//

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

//
//    Class CMCDictionary
//

function CMCDictionary()
{
    // Public properties
    
    this.mMap		= new Object();
    this.mOverflows	= new Array();
    this.mLength	= 0;
}

CMCDictionary.prototype.GetLength	= function( key )
{
	return this.mLength;
};

CMCDictionary.prototype.ForEach	= function( func )
{
	var map	= this.mMap;
	
	for ( var key in map )
	{
		var value	= map[key];
		
		if ( !func( key, value ) )
		{
			return;
		}
	}
	
	var overflows	= this.mOverflows;
	
	for ( var i = 0, length = overflows.length; i < length; i++ )
	{
		var item	= overflows[i];
		
		if ( !func( item.Key, item.Value ) )
		{
			return;
		}
	}
};

CMCDictionary.prototype.GetItem	= function( key )
{
	var item	= null;
	
	if ( typeof( this.mMap[key] ) == "function" )
	{
		var index	= this.GetItemOverflowIndex( key );
		
		if ( index >= 0 )
		{
			item = this.mOverflows[index].Value;
		}
	}
	else
	{
		item = this.mMap[key];
		
		if ( typeof( item ) == "undefined" )
		{
			item = null;
		}
	}

    return item;
};

CMCDictionary.prototype.GetItemOverflowIndex	= function( key )
{
	var overflows	= this.mOverflows;
	
	for ( var i = 0, length = overflows.length; i < length; i++ )
	{
		if ( overflows[i].Key == key )
		{
			return i;
		}
	}
	
	return -1;
}

CMCDictionary.prototype.Remove	= function( key )
{
	if ( typeof( this.mMap[key] ) == "function" )
	{
		var index	= this.GetItemOverflowIndex( key );
		
		if ( index >= 0 )
		{
			this.mOverflows.splice( index, 1 )
			
			this.mLength--;
		}
	}
	else
	{
		if ( this.mMap[key] != "undefined" )
		{
			delete( this.mMap[key] );
			
			this.mLength--;
		}
	}
};

CMCDictionary.prototype.Add	= function( key, value )
{
	if ( typeof( this.mMap[key] ) == "function" )
	{
		var item	= this.GetItem( key );
		
		if ( item != null )
		{
			this.Remove( key );
		}
		
		this.mOverflows[this.mOverflows.length] = { Key: key, Value: value };
	}
	else
	{
		this.mMap[key] = value;
    }
    
    this.mLength++;
};

CMCDictionary.prototype.AddUnique	= function( key, value )
{
	var savedValue	= this.GetItem( key );
	
	if ( typeof( savedValue ) == "undefined" || !savedValue )
	{
		this.Add( key, value );
	}
};

//
//    End class CMCDictionary
//

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

/* -CatapultCompiler- -Begin- -Copy to CSH Javascript- */

//
//    Class CMCUrl
//

function CMCUrl( src )
{
	// Private member variables
	
	var mSelf	= this;
	
	// Public properties

	this.FullPath			= null;
	this.Path				= null;
	this.PlainPath			= null;
	this.Name				= null;
	this.Extension			= null;
	this.NameWithExtension	= null;
	this.Fragment			= null;
	this.Query				= null;
	this.IsAbsolute			= false;

	// Constructor

	(function()
	{
		var fragment	= "";
		var query		= "";
		var fragmentPos	= src.indexOf( "#" );
		var queryPos	= src.indexOf( "?" );
		
		if ( fragmentPos != -1 )
		{
			if ( fragmentPos > queryPos )
			{
				fragment = src.substring( fragmentPos );
			}
			else
			{
				fragment = src.substring( fragmentPos, queryPos );
			}
		}
		
		if ( queryPos != -1 )
		{
			if ( queryPos > fragmentPos )
			{
				query = src.substring( queryPos );
			}
			else
			{
				query = src.substring( queryPos, fragmentPos );
			}
		}
		
		var pos			= Math.max( fragmentPos, queryPos );
		var plainPath	= src.substring( 0, pos == -1 ? src.length : pos );
		pos = plainPath.lastIndexOf( "/" );
		var path		= plainPath.substring( 0, pos + 1 );
		var nameWithExt	= plainPath.substring( pos + 1 );
		pos = nameWithExt.lastIndexOf( "." );
		var name		= nameWithExt.substring( 0, pos );
		var ext			= nameWithExt.substring( pos + 1 );
		
		var scheme		= "";
		pos = src.indexOf( ":" );
		
		if ( pos >= 0 )
		{
			scheme = src.substring( 0, pos );
		}
		
		mSelf.FullPath = src;
		mSelf.Path = path;
		mSelf.PlainPath = plainPath;
		mSelf.Name = name;
		mSelf.Extension = ext;
		mSelf.NameWithExtension = nameWithExt;
		mSelf.Scheme = scheme;
		mSelf.IsAbsolute = !String.IsNullOrEmpty( scheme );
		mSelf.Fragment = fragment;
		mSelf.Query = query;
	})();
}

// Public static properties

CMCUrl.QueryMap	= new CMCDictionary();
CMCUrl.HashMap	= new CMCDictionary();

(function()
{
	var search	= document.location.search;
	
	if ( !String.IsNullOrEmpty( search ) )
	{
		search = search.substring( 1 );
		Parse( search, "&", CMCUrl.QueryMap );
	}
	
	var hash	= document.location.hash;
	
	if ( !String.IsNullOrEmpty( hash ) )
	{
		hash = hash.substring( 1 );
		Parse( hash, "|", CMCUrl.HashMap );
	}
	
	function Parse( item, delimiter, map )
	{
		var split	= item.split( delimiter );
	
		for ( var i = 0, length = split.length; i < length; i++ )
		{
			var part	= split[i];
			var index	= part.indexOf( "=" );
			var key		= null;
			var value	= null;
			
			if ( index >= 0 )
			{
				key = part.substring( 0, index );
				value = part.substring( index + 1 );
			}
			else
			{
				key = part;
			}

			map.Add( key, value );
		}
	}
})();

//

CMCUrl.prototype.AddFile	= function( otherUrl )
{
	if ( typeof( otherUrl ) == "string" )
	{
		otherUrl = new CMCUrl( otherUrl );
	}
	
	if ( otherUrl.IsAbsolute )
	{
		return otherUrl;
	}
	
	var otherFullPath = otherUrl.FullPath;
	
	if ( otherFullPath.charAt( 0 ) == "/" )
	{
		var loc			= document.location;
		var pos			= loc.href.lastIndexOf( loc.pathname );
		var rootPath	= loc.href.substring( 0, pos );
		
		return new CMCUrl( rootPath + otherFullPath );
	}
	
	return new CMCUrl( this.FullPath + otherFullPath );
};

CMCUrl.prototype.ToFolder	= function()
{
	var fullPath	= this.FullPath;
	var pos			= fullPath.lastIndexOf( "/" );
	var fragmentPos	= fullPath.indexOf( "#" );
	var queryPos	= fullPath.indexOf( "?" );
	var minPos		= Math.min( fragmentPos, queryPos );
	var newPath		= fullPath.substring( 0, pos + 1 );

	if ( minPos >= 0 )
	{
		newPath = newPath + fullPath.substring( minPos );
	}

	return new CMCUrl( newPath );
};

CMCUrl.prototype.ToRelative	= function( otherUrl )
{
	var path		= otherUrl.FullPath;
	var otherPath	= this.FullPath;
	var pos			= otherPath.indexOf( path );
	var relPath		= null;
	
	if ( pos == 0 )
	{
		relPath = otherPath.substring( path.length );
	}
	else
	{
		relPath = otherPath;
	}
	
	return new CMCUrl( relPath );
};

CMCUrl.prototype.ToExtension	= function( newExt )
{
	var path	= this.FullPath;
	var pos		= path.lastIndexOf( "." );
	var left	= path.substring( 0, pos );
	var newPath	= left + "." + newExt;
	
	return new CMCUrl( newPath );
};

//
//    End class CMCUrl
//

/* -CatapultCompiler- -End- -Copy to CSH Javascript- */

//
//    DOM traversal functions
//

function FMCGetElementsByClassRoot( node, classRoot )
{
    var nodes   = new Array();
    var args    = new Array();
    
    args[0] = nodes;
    args[1] = classRoot;
    
    FMCTraverseDOM( "post", node, FMCGetByClassRoot, args );
                         
    return nodes;
}

function FMCGetByClassRoot( node, args )
{
    var nodes       = args[0];
    var classRoot   = args[1];
    
    if ( node.nodeType == 1 && FMCContainsClassRoot( node.className, classRoot ) )
    {
        nodes[nodes.length] = node;
    }
}

function FMCGetElementsByAttribute( node, attribute, value )
{
    var nodes   = new Array();
    var args    = new Array();
    
    args[0] = nodes;
    args[1] = attribute;
    args[2] = value;
    
    FMCTraverseDOM( "post", node, FMCGetByAttribute, args );
                         
    return nodes;
}

function FMCGetByAttribute( node, args )
{
    var nodes       = args[0];
    var attribute   = args[1];
    var value       = args[2];
    
    try
    {
        if ( node.nodeType == 1 && (FMCGetMCAttribute( node, attribute ) == value || (value == "*" && FMCGetMCAttribute( node, attribute ))) )
        {
            nodes[nodes.length] = node;
        }
    }
    catch( err )
    {
        node.setAttribute( attribute, null );
    }
}

function FMCTraverseDOM( type, root, Func, args )
{
    if ( type == "pre" )
    {
        Func( root, args );
    }
    
    if ( root.childNodes.length != 0 )
    {
        for ( var i = 0; i < root.childNodes.length; i++ )
        {
            FMCTraverseDOM( type, root.childNodes[i], Func, args );
        }
    }
    
    if ( type == "post" )
    {
        Func( root, args );
    }
}

//
//    End DOM traversal functions
//

//
//    Button effects
//

var gButton		= null;
var gTabIndex	= 1;

function MakeButton( td, title, outImagePath, overImagePath, selectedImagePath, width, height, text )
{
	var div	= document.createElement( "div" );
	
	div.tabIndex = gTabIndex++;
	
    title ? div.title = title : false;
    div.setAttribute( "MadCap:outImage", outImagePath );
    div.setAttribute( "MadCap:overImage", overImagePath );
    div.setAttribute( "MadCap:selectedImage", selectedImagePath );
    div.setAttribute( "MadCap:width", width );
    div.setAttribute( "MadCap:height", height );
    
    FMCPreloadImage( outImagePath );
    FMCPreloadImage( overImagePath );
    FMCPreloadImage( selectedImagePath );
    
    div.appendChild( document.createTextNode( text ) );
    td.appendChild( div );
    
    InitButton( div );
}

function InitButton( button )
{
	var width	= parseInt( FMCGetMCAttribute( button, "MadCap:width" ) ) + "px";
	var height	= parseInt( FMCGetMCAttribute( button, "MadCap:height" ) ) + "px";
	var image	= FMCGetMCAttribute( button, "MadCap:outImage" );
	
	if ( image != null )
	{
		if ( !image.StartsWith( "url", false ) || !image.EndsWith( ")", false ) )
		{
			image = FMCCreateCssUrl( image );
		}

		button.style.backgroundImage = image;
		
		button.onmouseover = ButtonOnOver;
		button.onmouseout = ButtonOnOut;
		button.onmousedown = ButtonOnDown;
	}
	
	button.style.cursor = "default";
	button.style.width = width;
	button.style.height = height;

	button.parentNode.style.width = width;
	button.parentNode.style.height = height;
}

function ButtonOnOver()
{
	var image	= FMCGetMCAttribute( this, "MadCap:overImage" );
	
	if ( !image.StartsWith( "url", false ) || !image.EndsWith( ")", false ) )
	{
		image = FMCCreateCssUrl( image );
	}
	
	this.style.backgroundImage = image;
}

function ButtonOnOut()
{
	var image	= FMCGetMCAttribute( this, "MadCap:outImage" );
	
	if ( !image.StartsWith( "url", false ) || !image.EndsWith( ")", false ) )
	{
		image = FMCCreateCssUrl( image );
	}
	
	this.style.backgroundImage = image;
}

function ButtonOnDown()
{
	StartPress( this ); return false;
}

function StartPress( node )
{
    // Debug
    //window.status += "s";
    
    gButton = node;
    
    if ( document.body.setCapture )
    {
        document.body.setCapture();
        
        document.body.onmousemove = Press;
        document.body.onmouseup = EndPress;
    }
    else if ( document.addEventListener )
    {
        document.addEventListener( "mousemove", Press, true );
        document.addEventListener( "mouseup", EndPress, true );
    }
    
    gButton.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( gButton, "MadCap:selectedImage" ) );
    gButton.onmouseover = function() { this.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( this, "MadCap:selectedImage" ) ); };
}

function Press( e )
{
    // Debug
    //window.status += "p";
    
    if ( !e )
    {
        e = window.event;
        target = e.srcElement;
    }
    else if ( e.target )
    {
        target = e.target;
    }
    
    if ( target == gButton )
    {
        gButton.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( gButton, "MadCap:selectedImage" ) );
    }
    else
    {
        gButton.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( gButton, "MadCap:outImage" ) );
    }
}

function EndPress( e )
{
    // Debug
    //window.status += "e";
    
    var target  = null;
    
    if ( !e )
    {
        e = window.event;
        target = e.srcElement;
    }
    else if ( e.target )
    {
        target = e.target;
    }
    
    if ( target == gButton )
    {
        // Debug
        //window.status += "c";
        
        gButton.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( gButton, "MadCap:overImage" ) );
    }
    
    gButton.onmouseover = function() { this.style.backgroundImage = FMCCreateCssUrl( FMCGetMCAttribute( this, "MadCap:overImage" ) ); };
    
    if ( document.body.releaseCapture )
    {
        document.body.releaseCapture();
        
        document.body.onmousemove = null;
        document.body.onmouseup = null;
    }
    else if ( document.removeEventListener )
    {
        document.removeEventListener( "mousemove", Press, true );
        document.removeEventListener( "mouseup", EndPress, true );
    }
    
    gButton = null;
}

//
//    End button effects
//

if ( FMCIsWebHelpAIR() )
{
	gOnloadFuncs.splice( 0, 0, FMCInitializeBridge );

	function FMCInitializeBridge()
	{
		if ( window.parentSandboxBridge )
		{
			if ( typeof( gServiceClient ) != "undefined" )
			{
				gServiceClient = {};
			}
			
			for ( var key in window.parentSandboxBridge )
			{
				var pairs		= key.split( "_" );
				var ns			= pairs[0];
				var funcName	= pairs[1];
				
				if ( ns == "FeedbackServiceClient" )
				{
					if ( typeof( gServiceClient ) != "undefined" )
					{
						gServiceClient[funcName] = window.parentSandboxBridge[key];
					}
				}
				else if ( ns == "MadCapUtilities" )
				{
					window[funcName] = window.parentSandboxBridge[key];
				}
			}
		}
	}
}

var MCFader	= new function()
{
	// Public methods

	this.FadeIn	= function( node, startOpacity, endOpacity, nodeBG, startOpacityBG, endOpacityBG, handleClick )
	{
		var interval	= 0;
		
		var opacityStep = (endOpacity - startOpacity) / 10;
		var opacityStepBG = (endOpacityBG - startOpacityBG) / 10;

		FMCSetOpacity( node, startOpacity );
		FMCSetOpacity( nodeBG, startOpacityBG );

		function DoFadeIn()
		{
			var opacity	= FMCGetOpacity( node );
			
			if ( opacity == startOpacity || opacity == -1 )
			{
				if ( handleClick )
				{
					var funcIndex	= -1;
					
					function OnClickDocument()
					{
						node.parentNode.removeChild( node );
						nodeBG.parentNode.removeChild( nodeBG );
						
						gDocumentOnclickFuncs.splice( funcIndex, 1 );
					}
					
					funcIndex = gDocumentOnclickFuncs.push( OnClickDocument ) - 1;
				}
			}
			
			if ( opacity == -1 )
			{
				clearInterval( interval );
				
				return;
			}
			
			var newOpacity = opacity + opacityStep;
			var opacityBG = FMCGetOpacity( nodeBG );

			FMCSetOpacity( node, newOpacity );
			FMCSetOpacity( nodeBG, opacityBG + opacityStepBG );

			if ( newOpacity >= endOpacity )
			{
				clearInterval( interval );
			}
		}

		interval = setInterval( DoFadeIn, 10 );
	};
}

//
//    Class CMCDateTimeHelpers
//

var CMCDateTimeHelpers = new function()
{
	this.GetDateFromUTCString = function( utcString )
	{
		var ms		= Date.parse( utcString );
		var date	= new Date( ms );
		var utcMS	= Date.UTC( date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds(), date.getMilliseconds() );
		var utcDate	= new Date( utcMS );
		
		return utcDate;
	};
	
	this.ToUIString = function( date )
	{
		var dateStr = (date.getMonth() + 1) + "/" + date.getDate() + "/" + date.getFullYear() + " " + date.toLocaleTimeString();

		return dateStr;
	};
}

//
//    End class CMCDateTimeHelpers
//

//
//    Class CMCException
//

function CMCException( number, message )
{
	// Private member variables and functions

	this.Number		= number;
	this.Message	= message;
}

//
//    End class CMCException
//
