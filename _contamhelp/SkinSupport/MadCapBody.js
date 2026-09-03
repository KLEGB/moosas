/// <reference path="MadCapUtilities.js" />
/// <reference path="MadCapLiveHelpUtilities.js" />

// {{MadCap}} //////////////////////////////////////////////////////////////////
// Copyright: MadCap Software, Inc - www.madcapsoftware.com ////////////////////
////////////////////////////////////////////////////////////////////////////////
// <version>4.2.0.0</version>
////////////////////////////////////////////////////////////////////////////////

//

if ( FMCIsDotNetHelp() || FMCIsHtmlHelp() )
{
	window.name = "body";
}

//

gOnloadFuncs.push( FMCInit );

//

var gInit	= false;

function FMCInit()
{
	if ( gInit )
	{
		return;
	}

	//

	FMCCheckForBookmark();

	if ( FMCIsWebHelp() && window.name == "body" )
	{
		FMCRegisterCallback( "TOC", MCEventType.OnInit, FMCOnTocInitialized, null );
	}
	
	if ( MCGlobals.ToolbarFrame != null )
	{
		FMCRegisterCallback( "Toolbar", MCEventType.OnInit, FMCOnToolbarLoaded, null );
	}
	
	if ( MCGlobals.BodyCommentsFrame != null && !FMCIsTopicPopup( window ) )
	{
		FMCRegisterCallback( "BodyComments", MCEventType.OnLoad, FMCOnBodyCommentsLoaded, null );
	}
	
	if ( MCGlobals.TopicCommentsFrame != null )
	{
		FMCRegisterCallback( "TopicComments", MCEventType.OnInit, FMCOnTopicCommentsInit, null );
	}
	
	if ( MCGlobals.RecentCommentsFrame != null )
	{
		FMCRegisterCallback( "RecentComments", MCEventType.OnInit, FMCOnRecentCommentsInit, null );
	}
	
	var rootFrame	= FMCGetRootFrame();

	if ( rootFrame )
	{
		rootFrame.FMCHighlightUrl( window );
	}
	else if ( typeof( FMCHighlightUrl ) != "undefined" )
	{
		FMCHighlightUrl( window );
	}
	
	//

	if ( MCGlobals.RootFrame == null && !FMCIsTopicPopup( window ) )
	{
		var framesetLinks	= FMCGetElementsByClassRoot( document.body, "MCWebHelpFramesetLink" );
		
		for ( var i = 0; i < framesetLinks.length; i++ )
		{
			var framesetLink	= framesetLinks[i];
			framesetLink.style.display = "";
		}
	}

	//

	if ( typeof( gServiceClient ) != "undefined" && typeof( gServiceClient.LogTopic ) == "function" && !FMCIsSkinPreviewMode() )
	{
		gServiceClient.GetVersion( function( version )
		{
			var topicID	= FMCGetMCAttribute( document.documentElement, "MadCap:liveHelp" );
			
			if ( version == 1 )
			{
				gServiceClient.LogTopic( topicID );
			}
			else
			{
				var cshID	= CMCUrl.QueryMap.GetItem( "CSHID" );
				
				gServiceClient.LogTopic2( topicID, cshID, null, null, null );
			}
		}, null, null );
	}

	//

	gInit = true;
}

function FMCOnTocInitialized()
{
	if ( MCGlobals.NavigationFrame.frames["toc"].gSyncTOC )
    {
        FMCSyncTOC();
    }
}

function FMCOnToolbarLoaded()
{
	if ( FMCIsLiveHelpEnabled() && MCGlobals.ToolbarFrame.document.getElementById( "RatingIcons" ) != null )
	{
		MCGlobals.ToolbarFrame.SetRating( 0 );
		
		FMCUpdateToolbarRating();
	}
}

function FMCUpdateToolbarRating()
{
	var topicID	= FMCGetMCAttribute( document.documentElement, "MadCap:liveHelp" );

	gServiceClient.GetAverageRating( topicID, FMCBodyGetRatingOnComplete, null );
}

function FMCOnBodyCommentsLoaded()
{
	MCGlobals.BodyCommentsFrame.Init( OnInit );
	
	function OnInit()
	{
		MCGlobals.BodyCommentsFrame.RefreshComments();
	}
}

function FMCOnTopicCommentsInit()
{
	var helpSystem	= FMCGetHelpSystem();
	
	if ( helpSystem.LiveHelpEnabled )
	{
		var topicCommentsFrame	= MCGlobals.TopicCommentsFrame;

		topicCommentsFrame.RefreshComments();
	}
}

function FMCOnRecentCommentsInit()
{
	var recentCommentsFrame	= MCGlobals.RecentCommentsFrame;

	recentCommentsFrame.RefreshComments();
}

function FMCBodyGetRatingOnComplete( averageRating, ratingCount, onCompleteArgs )
{
	var toolbarFrame	= MCGlobals.ToolbarFrame;
	
	toolbarFrame.SetRating( averageRating );
}

function FMCCheckForBookmark()
{
    var hash	= document.location.hash;
    
    if ( !hash )
    {
        return;
    }
    
    var bookmark	= null;
    
    if ( hash.charAt( 0 ) == "#" )
    {
        hash = hash.substring( 1 );
    }
    
    var currAnchor  = null;
    
    for ( var i = 0; i < document.anchors.length; i++ )
    {
        currAnchor = document.anchors[i];
        
        if ( currAnchor.name == hash )
        {
            bookmark = currAnchor;
            
            break;
        }
    }
    
    if ( bookmark )
    {
        FMCUnhide( window, currAnchor );
        
        // Mozilla didn't navigate to the bookmark on load since it was inside a hidden node. So, after we ensure it's visible, navigate to the bookmark again.
        
        if ( !document.body.currentStyle )
        {
            document.location.href = document.location.href;
        }
        
        if ( navigator.userAgent.Contains( "MSIE 7", false ) )
        {
			// IE 7 bug: Older builds of IE 7 have the following bug: if you create an iframe who's URL has a bookmark and the iframe's opacity has been set,
			// the document won't scroll to the bookmark. It seems to be a render issue because scrolling the document in the iframe causes it to jump down to
			// the bookmark and scroll from there. The hack workaround is to cause the iframe to redraw after the document has loaded, which is done here.
	        
	        window.setTimeout( function()
	        {
				document.body.style.display = "none";
				document.body.style.display = "";
			}, 1 );
        }
    }
}

function FMCSyncTOC()
{
    if ( !MCGlobals.NavigationFrame.frames["toc"] || MCGlobals.BodyFrame.document != document )
    {
        return;
    }
    
    var tocPath = FMCGetMCAttribute( document.documentElement, "MadCap:tocPath" );
    
    MCGlobals.NavigationFrame.frames["toc"].SyncTOC( tocPath );
}

function FMCGlossaryTermHyperlinkOnClick( node )
{
    var navFrame	= MCGlobals.NavigationFrame;
    var anchorName	= FMCGetMCAttribute( node, "MadCap:anchor" );
    
    navFrame.SetActiveIFrameByName( "glossary" );
    navFrame.frames["glossary"].DropDownTerm( anchorName );
}

function FMCGetHelpSystem()
{
	var src					= document.location.href;
	var pathToHelpSystem	= FMCGetAttribute( document.documentElement, "MadCap:PathToHelpSystem" );
	var pos					= src.lastIndexOf( "/" );
	var parentPath			= src.substring( 0, pos + 1 );
	
	if ( pathToHelpSystem == null )
	{
		pathToHelpSystem = "";
	}
	
	parentPath += pathToHelpSystem;
	
	return new MCGlobals.RootFrame.CMCHelpSystem( null, parentPath, parentPath + MCGlobals.SubsystemFile, null );
}
