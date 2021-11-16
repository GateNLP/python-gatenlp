from gatenlp.processing.gazetteer.stringregex import StringRegexAnnotator

default_tokenizer_rules = r"""
#words#
// a word can be any combination of letters, including hyphens,
// but excluding symbols and punctuation, e.g. apostrophes
// Note that there is an alternative version of the tokeniser that
// treats hyphens as separate tokens


|(?:\p{Lu}(?:\p{Mn})*)(?:(?:\p{Ll}(?:\p{Mn})*)(?:(?:\p{Ll}(?:\p{Mn})*)|\p{Pd}|\p{Cf})*)*
0 =>  Token orth="upperInitial", kind="word", 

|(?:\p{Lu}(?:\p{Mn})*)(?:\p{Pd}|\p{Cf})*(?:(?:\p{Lu}(?:\p{Mn})*)|\p{Pd}|\p{Cf})+
0 =>  Token orth="allCaps", kind="word", 

|(?:\p{Ll}(?:\p{Mn})*)(?:(?:\p{Ll}(?:\p{Mn})*)|\p{Pd}|\p{Cf})*
0 =>  Token orth="lowercase", kind="word", 

// MixedCaps is any mixture of caps and small letters that doesn't
// fit in the preceding categories

|(?:(?:\p{Ll}(?:\p{Mn})*)(?:\p{Ll}(?:\p{Mn})*)+(?:\p{Lu}(?:\p{Mn})*)+(?:(?:\p{Lu}(?:\p{Mn})*)|(?:\p{Ll}(?:\p{Mn})*))*)|(?:(?:\p{Ll}(?:\p{Mn})*)(?:\p{Ll}(?:\p{Mn})*)*(?:\p{Lu}(?:\p{Mn})*)+(?:(?:\p{Lu}(?:\p{Mn})*)|(?:\p{Ll}(?:\p{Mn})*)|\p{Pd}|\p{Cf})*)|(?:(?:\p{Lu}(?:\p{Mn})*)(?:\p{Pd})*(?:\p{Lu}(?:\p{Mn})*)(?:(?:\p{Lu}(?:\p{Mn})*)|(?:\p{Ll}(?:\p{Mn})*)|\p{Pd}|\p{Cf})*(?:(?:\p{Ll}(?:\p{Mn})*))+(?:(?:\p{Lu}(?:\p{Mn})*)|(?:\p{Ll}(?:\p{Mn})*)|\p{Pd}|\p{Cf})*)|(?:(?:\p{Lu}(?:\p{Mn})*)(?:\p{Ll}(?:\p{Mn})*)+(?:(?:\p{Lu}(?:\p{Mn})*)+(?:\p{Ll}(?:\p{Mn})*)+)+)|(?:(?:(?:\p{Lu}(?:\p{Mn})*))+(?:(?:\p{Ll}(?:\p{Mn})*))+(?:(?:\p{Lu}(?:\p{Mn})*))+)
0 =>  Token orth="mixedCaps", kind="word", 

|(?:\p{Lo}|\p{Mc}|\p{Mn})+
0 => Token kind="word", type="other", 

#numbers#
// a number is any combination of digits
|\p{Nd}+
0 => Token kind="number", 

|\p{No}+
0 => Token kind="number", 

#whitespace#
|(?:\p{Zs}) 
0 => SpaceToken kind="space", 

|(?:\p{Cc}) 
0 => SpaceToken kind="control", 

#symbols#
|(?:\p{Sk}|\p{Sm}|\p{So}) 
0 =>  Token kind="symbol", 

|\p{Sc} 
0 =>  Token kind="symbol", symbolkind="currency", 

#punctuation#
|(?:\p{Pd}|\p{Cf}) 
0 => Token kind="punctuation", subkind="dashpunct", 

|(?:\p{Pc}|\p{Po})
0 => Token kind="punctuation", 

|(?:\p{Ps}|\p{Pi}) 
0 => Token kind="punctuation", position="startpunct", 

|(?:\p{Pe}|\p{Pf}) 
0 => Token kind="punctuation", position="endpunct", 
"""

default_tokenizer = StringRegexAnnotator(source=default_tokenizer_rules, source_fmt="string", select_rules="first",
                                         skip_longest=True, longest_only=True, regex_module="regex",
                                         )

alternate_tokenizer_rules = """
"""


