
class StringScanner
  def initialize(_s)
    raise TypeError if !_s
    @s = _s
    @index = 0
  end
  def string
    @s
  end
  def scan(r) 
    m = do_match(r)
#    puts("scan " + r.to_s + " '" + m.to_s + "', " + @index.to_s + ", " + (m ? m.end(0).to_s : "nil"))
    if m
      @index += m.end(0)
      return m[0]
    end
  end
  def skip(r)
    m = do_match(r)
    if m
      @index += m.end(0)
      return m[0].length
    end
  end
  def match?(r)
    m = do_match(r)
    if m
      return m[0].length
    end
  end
  def peek(len)
    @s[@index..(@index+len-1)]
  end
  def eos?
    if @s
      return @index == @s.length
    else 
      return 0
    end
  end
  def reset
    @index = 0
  end
  def [](n)
    @match[n]
  end
  
  private 
  
  def do_match(r)
    @match = Regexp.new("^"+r.to_s).match(@s[@index..-1])
    @match
  end
end
