# This "ifdef" is needed for SKP2014 compatibility
# We only need to include our Moosas/lib/json library for SKP8 and SKP2013
# Since SKP2014 uses Ruby 2.0.0 and has JSON support built-in

unless defined? JSON
  begin 

    # sometimes Ruby 2.0.0 doesn't have json required by default, check if we can do that first
    require 'json'

  rescue LoadError => e

    Sketchup::require('Moosas/lib/json/common')

    module JSON
       Sketchup::require('Moosas/lib/json/version')
       Sketchup::require('Moosas/lib/json/pure')
    end

  end
end
