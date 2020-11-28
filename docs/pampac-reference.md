# PAMPAC Reference 

This gives an overview over all the parsers, actions and helpers in the `pampac` module.

## Pampac

The two main components of Pampac are the rules and the pampac matcher:

[`Pampac`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Pampac
): the matcher which will match one or more rules against a document and annotations and fire the actions associated with matching rules. 


[`Rule`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Rule): a rule consists of a parser which describes the pattern to match in the document, and an action which will be carried out if the rule matches. 


## Parsers

Parsers are basic parsers which match annotations or text or combine basic parsers to match more complex patterns. 

[`And`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.And): combines to parsers and matches only if both match at the same location. 

[`Ann`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Ann): match an annotation with the given properties at the next index in the annotation list, or match the first annotation which starts at the current text offset.

[`AnnAt`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.AnnAt): match an annotation with the given properties at the offset at which the next annotation in the annotation list starts, or at the current text offset.

[`Call`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Call): call a function when the given parser matches, optionally call a function when the parser fails. 

[`Filter`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Filter): call a function for all results if the parser is successful and keep those results for which the function returns true. If at least one result was kept, succeed, otherwise fail. 

[`Find`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Find): from the current location, attempt to match the given parser at each text offset or at each annotation index until it matches and returns success or the end of the doccument is reached and it fails. 

[`Lookahead`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Lookahead): match a parser only if another parser matches after it, but do not consume or use the match after it. 

[`N`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.N): match a parser at least a certain min number of times but not more often than a max number of times, optionally only until another parser matches. 

[`Or`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Or): try to match each of the parsers in sequence and return success as soon as a parser matches. If no parser matches return failure. 

[`Seq`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Seq): match the all the parsers in sequence. 

[`Text`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.Text): match the given text or regular expression against the document text. 


## Actions 

Actions are classes that provide a simple way to perform an action if a rule fires. 

[`AddAnn`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.AddAnn): Add a new annotation. 

[`UpdateAnnFeatures`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.UpdateAnnFeatures): update the features of an existing annotation. 

## Helpers 

Helpers are classes which can be used with Actions to simplify accessing information from matches in a parse result. 

[`GetAnn`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetAnn): retrieve an annotation that was matched in the result

[`GetEnd`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetEnd): get the end offset of an annotation that was matched in the result

[`GetFeature`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetFeature): get a specific feature of an annotation that was matched in the result. 

[`GetFeatures`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetFeatures): get a feature set of an annotation that was matched in the result

[`GetRegexpGroup`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetRegexGroup): get the text for a regular expression group that was matched in the result. 

[`GetStart`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetStart): get the start offset of an annotation that was matched in the result

[`GetText`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetText): get the text that was matched in the result

[`GetType`](https://gatenlp.github.io/python-gatenlp/pythondoc/gatenlp/pam/pampac.html#gatenlp.pam.pampac.GetType): get the type of an annotation that was matched in the result.

