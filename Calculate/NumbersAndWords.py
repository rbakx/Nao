# Copyright (c) 2003, Taro Ogawa.  All Rights Reserved.
# Copyright (c) 2013, Savoir-faire Linux inc.  All Rights Reserved.

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA

from __future__ import unicode_literals


class OrderedMapping(dict):
    def __init__(self, *pairs):
        self.order = []
        for key, val in pairs:
            self[key] = val
    
    def __setitem__(self, key, val):
        if key not in self:
            self.order.append(key)
        super(OrderedMapping, self).__setitem__(key, val)
    
    def __iter__(self):
        for item in self.order:
            yield item
    
    def __repr__(self):
        out = ["%s: %s"%(repr(item), repr(self[item])) for item in self]
        out = ", ".join(out)
        return "{%s}"%out


class Num2Word_Base(object):
    def __init__(self):
        self.cards = OrderedMapping()
        self.is_title = False
        self.precision = 2
        self.exclude_title = []
        self.negword = "(-) "
        self.pointword = "(.)"
        self.errmsg_nonnum = "type(%s) not in [long, int, float]"
        self.errmsg_floatord = "Cannot treat float %s as ordinal."
        self.errmsg_negord = "Cannot treat negative num %s as ordinal."
        self.errmsg_toobig = "abs(%s) must be less than %s."
        
        self.base_setup()
        self.setup()
        self.set_numwords()
        
        self.MAXVAL = 1000 * self.cards.order[0]
    
    
    def set_numwords(self):
        self.set_high_numwords(self.high_numwords)
        self.set_mid_numwords(self.mid_numwords)
        self.set_low_numwords(self.low_numwords)
    
    
    def gen_high_numwords(self, units, tens, lows):
        out = [u + t for t in tens for u in units]
        out.reverse()
        return out + lows
    
    
    def set_mid_numwords(self, mid):
        for key, val in mid:
            self.cards[key] = val
    
    
    def set_low_numwords(self, numwords):
        for word, n in zip(numwords, range(len(numwords) - 1, -1, -1)):
            self.cards[n] = word
    
    
    def splitnum(self, value):
        for elem in self.cards:
            if elem > value:
                continue
            
            out = []
            if value == 0:
                div, mod = 1, 0
            else:
                div, mod = divmod(value, elem)
            
            if div == 1:
                out.append((self.cards[1], 1))
            else:
                if div == value:  # The system tallies, eg Roman Numerals
                    return [(div * self.cards[elem], div*elem)]
                out.append(self.splitnum(div))
            
            out.append((self.cards[elem], elem))
            
            if mod:
                out.append(self.splitnum(mod))
            
            return out
    
    
    def to_cardinal(self, value):
        try:
            assert long(value) == value
        except (ValueError, TypeError, AssertionError):
            return self.to_cardinal_float(value)
        
        self.verify_num(value)
        
        out = ""
        if value < 0:
            value = abs(value)
            out = self.negword
        
        if value >= self.MAXVAL:
            raise OverflowError(self.errmsg_toobig % (value, self.MAXVAL))
        
        
        val = self.splitnum(value)
        words, num = self.clean(val)
        return self.title(out + words)
    
    
    def to_cardinal_float(self, value):
        try:
            float(value) == value
        except (ValueError, TypeError, AssertionError):
            raise TypeError(self.errmsg_nonnum % value)
        
        pre = int(value)
        post = abs(value - pre)
        
        out = [self.to_cardinal(pre)]
        if self.precision:
            out.append(self.title(self.pointword))
        
        for i in range(self.precision):
            post *= 10
            curr = int(post)
            out.append(str(self.to_cardinal(curr)))
            post -= curr
        
        return " ".join(out)
    
    
    def merge(self, curr, next):
        raise NotImplementedError
    
    
    def clean(self, val):
        out = val
        while len(val) != 1:
            out = []
            left, right = val[:2]
            if isinstance(left, tuple) and isinstance(right, tuple):
                out.append(self.merge(left, right))
                if val[2:]:
                    out.append(val[2:])
            else:
                for elem in val:
                    if isinstance(elem, list):
                        if len(elem) == 1:
                            out.append(elem[0])
                        else:
                            out.append(self.clean(elem))
                    else:
                        out.append(elem)
            val = out
        return out[0]
    
    
    def title(self, value):
        if self.is_title:
            out = []
            value = value.split()
            for word in value:
                if word in self.exclude_title:
                    out.append(word)
                else:
                    out.append(word[0].upper() + word[1:])
            value = " ".join(out)
        return value
    
    
    def verify_ordinal(self, value):
        if not value == long(value):
            raise TypeError, self.errmsg_floatord %(value)
        if not abs(value) == value:
            raise TypeError, self.errmsg_negord %(value)
    
    
    def verify_num(self, value):
        return 1
    
    
    def set_wordnums(self):
        pass
    
    
    def to_ordinal(value):
        return self.to_cardinal(value)
    
    
    def to_ordinal_num(self, value):
        return value
    
    
    # Trivial version
    def inflect(self, value, text):
        text = text.split("/")
        if value == 1:
            return text[0]
        return "".join(text)
    
    
    #//CHECK: generalise? Any others like pounds/shillings/pence?
    def to_splitnum(self, val, hightxt="", lowtxt="", jointxt="",
                    divisor=100, longval=True, cents = True):
        out = []
        try:
            high, low = val
        except TypeError:
            high, low = divmod(val, divisor)
        if high:
            hightxt = self.title(self.inflect(high, hightxt))
            out.append(self.to_cardinal(high))
            if low:
                if longval:
                    if hightxt:
                        out.append(hightxt)
                    if jointxt:
                        out.append(self.title(jointxt))
            elif hightxt:
                out.append(hightxt)
        if low:
            if cents:
                out.append(self.to_cardinal(low))
            else:
                out.append("%02d" % low)
            if lowtxt and longval:
                out.append(self.title(self.inflect(low, lowtxt)))
        return " ".join(out)
    
    
    def to_year(self, value, **kwargs):
        return self.to_cardinal(value)
    
    
    def to_currency(self, value, **kwargs):
        return self.to_cardinal(value)
    
    
    def base_setup(self):
        pass
    
    
    def setup(self):
        pass
    
    
    def test(self, value):
        try:
            _card = self.to_cardinal(value)
        except:
            _card = "invalid"
        
        try:
            _ord = self.to_ordinal(value)
        except:
            _ord = "invalid"
        
        try:
            _ordnum = self.to_ordinal_num(value)
        except:
            _ordnum = "invalid"
        
        print ("For %s, card is %s;\n\tord is %s; and\n\tordnum is %s." %
               (value, _card, _ord, _ordnum))

class Num2Word_EU(Num2Word_Base):
    def set_high_numwords(self, high):
        max = 3 + 6*len(high)
        
        for word, n in zip(high, range(max, 3, -6)):
            self.cards[10**n] = word + "illiard"
            self.cards[10**(n-3)] = word + "illion"
    
    
    def base_setup(self):
        lows = ["non","oct","sept","sext","quint","quadr","tr","b","m"]
        units = ["", "un", "duo", "tre", "quattuor", "quin", "sex", "sept",
                 "octo", "novem"]
        tens = ["dec", "vigint", "trigint", "quadragint", "quinquagint",
                         "sexagint", "septuagint", "octogint", "nonagint"]
        self.high_numwords = ["cent"]+self.gen_high_numwords(units, tens, lows)
    
    def to_currency(self, val, longval=True, jointxt=""):
        return self.to_splitnum(val, hightxt="Euro/s", lowtxt="Euro cent/s",
                                jointxt=jointxt, longval=longval)



class Num2Word_EN(Num2Word_EU):
    def set_high_numwords(self, high):
        max = 3 + 3*len(high)
        for word, n in zip(high, range(max, 3, -3)):
            self.cards[10**n] = word + "illion"
    
    def setup(self):
        self.negword = "minus "
        self.pointword = "point"
        self.errmsg_nornum = "Only numbers may be converted to words."
        self.exclude_title = ["and", "point", "minus"]
        
        self.mid_numwords = [(1000, "thousand"), (100, "hundred"),
                             (90, "ninety"), (80, "eighty"), (70, "seventy"),
                             (60, "sixty"), (50, "fifty"), (40, "forty"),
                             (30, "thirty")]
        self.low_numwords = ["twenty", "nineteen", "eighteen", "seventeen",
                                                  "sixteen", "fifteen", "fourteen", "thirteen",
                                                  "twelve", "eleven", "ten", "nine", "eight",
                                                  "seven", "six", "five", "four", "three", "two",
                                                  "one", "zero"]
        self.ords = { "one"    : "first",
                                                      "two"    : "second",
                                                      "three"  : "third",
                                                      "five"   : "fifth",
                                                      "eight"  : "eighth",
                                                      "nine"   : "ninth",
                                                      "twelve" : "twelfth" }
    
    
    def merge(self, (ltext, lnum), (rtext, rnum)):
        if lnum == 1 and rnum < 100:
            return (rtext, rnum)
        elif 100 > lnum > rnum :
            return ("%s-%s"%(ltext, rtext), lnum + rnum)
        elif lnum >= 100 > rnum:
            return ("%s and %s"%(ltext, rtext), lnum + rnum)
        elif rnum > lnum:
            return ("%s %s"%(ltext, rtext), lnum * rnum)
        return ("%s, %s"%(ltext, rtext), lnum + rnum)
    
    
    def to_ordinal(self, value):
        self.verify_ordinal(value)
        outwords = self.to_cardinal(value).split(" ")
        lastwords = outwords[-1].split("-")
        lastword = lastwords[-1].lower()
        try:
            lastword = self.ords[lastword]
        except KeyError:
            if lastword[-1] == "y":
                lastword = lastword[:-1] + "ie"
            lastword += "th"
        lastwords[-1] = self.title(lastword)
        outwords[-1] = "-".join(lastwords)
        return " ".join(outwords)
    
    
    def to_ordinal_num(self, value):
        self.verify_ordinal(value)
        return "%s%s"%(value, self.to_ordinal(value)[-2:])
    
    
    def to_year(self, val, longval=True):
        if not (val//100)%10:
            return self.to_cardinal(val)
        return self.to_splitnum(val, hightxt="hundred", jointxt="and",
                                longval=longval)
    
    def to_currency(self, val, longval=True):
        return self.to_splitnum(val, hightxt="dollar/s", lowtxt="cent/s",
                                jointxt="and", longval=longval, cents = True)

CONVERTER_CLASSES = {
    'en': Num2Word_EN()

}

def num2words(number, ordinal=False, lang='en'):
    # We try the full language first
    if lang not in CONVERTER_CLASSES:
        # ... and then try only the first 2 letters
        lang = lang[:2]
    if lang not in CONVERTER_CLASSES:
        raise NotImplementedError()
    converter = CONVERTER_CLASSES[lang]
    if ordinal:
        return converter.to_ordinal(number)
    else:
        return converter.to_cardinal(number)


def words2num(s):
    """
        Converts strings to numbers (up to 999 999)
        @accepts: str
        @returns: int
        @throws: ValueError (can't figure out)
        
        four -> 4
        five -> 5
        thousand -> 1000
        five thousand and sixty seven > 5067
        
        numbers remain numbers:
        
        3456 -> 3456
        
        """
    primitives = dict(zip("one two three four five six seven eight nine".split(), range(1, 11)))
    teens = dict(zip("eleven twelve thirteen fourteen sixteen seventeen eighteen nineteen".split(), range(11, 20)))
    tens = dict(zip("ten twenty thirty fourty fifty sixty seventy eighty ninety".split(), range(10, 100, 10)))
    multiples = dict(zip("hundred thousand".split(), [1e2, 1e3]))
    
    def primitive(a):
        if a in primitives:
            return primitives[a]
        elif a in tens:
            return tens[a]
        elif a in teens:
            return teens[a]
        elif a in multiples:
            return multiples[a]
        raise ValueError
    
    def up2hundred(tokens):
        if len(tokens) == 2:
            return primitive(tokens[0]) + primitive(tokens[1])
        elif len(tokens) == 1:
            a = tokens[0]
            return primitive(a)
        raise ValueError
    
    def up2thousand(tokens):
        if "hundred" in tokens:
            i = tokens.index("hundred")
            return up2hundred(tokens[:i]) * 100 + up2hundred(tokens[i+1:])
        else:
            return up2hundred(tokens)
        raise ValueError
    
    def up2million(tokens):
        if "thousand" in tokens:
            i = tokens.index("thousand")
            return up2thousand(tokens[:i]) * 1000 + up2thousand(tokens[i+1:])
        return up2thousand(tokens)
    
    try:
        return int(s)
    except ValueError:
        s = s.replace("-", " ")
        tokens = [t for t in s.split() if not t in ("and", " ")]
        
        return up2million(tokens)