unless defined?(::JSON::JSON_LOADED) and ::JSON::JSON_LOADED
  Sketchup::require('Moosas/lib/json')
end
defined?(::Rational) or Sketchup::require('Moosas/lib/rational')

class Rational
  def self.json_create(object)
    Rational(object['n'], object['d'])
  end

  def as_json(*)
    {
      JSON.create_id => self.class.name,
      'n'            => numerator,
      'd'            => denominator,
    }
  end

  def to_json(*)
    as_json.to_json
  end
end
