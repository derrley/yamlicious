
.. image:: https://travis-ci.org/derrley/yamlicious.png

Yamlicious is a (work-in-progress) lightweight configuration library built on
top of YAML. It's for folks who love to write their configuration files in
YAML, but who find themselves writing additional boilerplate each time they
want to use YAML to encode a configuration file.

In addition to a parser, yamlicious provides code that:

- Validates the correctness of a file and prints an understandable failure
  message when the file doesn't quite match

- Understands your environemnt, and allows you to configure different properties
  for different environment dimensions without unnecessary DRY-violation

- Reads configuration from multiple files

- Provides a cascading set of configuration sources, including environment
  variables

- Lazily loads certain parts of a large configuration. (read: when your
  "configuration" really starts to feel more like "data.")

- Is generically extensible to new behavior, just in case you need to add
  something we haven't thought of

Yamlicious does all this by being like any other YAML parser, but by treating a
handful of specific keys in a special way. It can be configured to recognize
and evaluate any subset of these *feature keys*, allowing a developer to bake
in as much (or as little!) of the crazy capabilities as seems reasonable for
the situation. (The craziest stuff is turned off by default.)

Skip to `Feature Key Definitions`_ if you want the formality without the
English verbiage.

.. contents::


The Yamlicious File
====================

A configuration file specified in Yamlicious *is just YAML*. In fact, nothing stops
you from parsing a Yamlicious file with any YAML library. This can be useful for
searching, cleaning, or editing (with syntax highlighting) the file.

Environment Variable Subtitution
---------------------------------

Yamlicious gives your configuration file automatic access to the environment. 

.. code-block:: yaml

  some:
    key:
      user_$(USER): not cool
      user_kyle: cool

Don't worry. The Yamlicious API gives you (the developer) the ability to both
limit the environment variables your configuration file is allowed to access
and provide overriding values for anything in the environment. You're neither
forced to use environment variables nor doomed to a free for all.

Yamlicious supports list values in the environment, and splits environment variables
on the comma character. If a Yamlicious file substitutes a list variable into a
string, that string renders into multiple strings (one for each value in the
list variable).

If a string references a variable that's not in the environment, yamlicious
does not modify the string. It will leave the variable reference alone, ``$()``
characters included. This makes string substitution have a neat property -- it
can be applied to the same document iteratively as the environment grows.

List substitution behavior varies subtly by situation.


When substituting into a single value string
````````````````````````````````````````````

.. code-block:: yaml

  some_list: $(MY_LIST)

renders to the following, if ``MY_LIST=one,two,three`` is in the environment.

.. code-block:: yaml

  some_list:
    - one
    - two
    - three


When substituting into a value list
```````````````````````````````````

.. code-block:: yaml

  some_list:
    - first
    - $(LIST)

becomes

.. code-block:: yaml

  some_list:
    - first
    - one
    - two
    - three


When substituting into a key string
```````````````````````````````````

Key strings are special, because you almost certainly don't intend to make a
list into the key of a dictionary. Instead, you likely mean to define a key in
the dictionary for each item in the list. Yamlicious provides a special
variable in the environment, ``_KEY``, to help you out in this situation.

.. code-block:: yaml

  $(LIST): $(_KEY) is in the list!

becomes

.. code-block:: yaml

  one: one is in the list
  two: two is in the list
  three: three is in the list

``_KEY`` is set to the first-level key in the document, regardless of whether
the key was derived from string substitution. To get the second-level key, use
``__KEY``, and so forth:

.. code-block:: yaml

  $(LIST):
    second_level_key: $(_KEY) on top and $(__KEY) on bottom

becomes

.. code-block:: yaml

  one:
    second_level_key: one on top and second_level_key on bottom
  two:
    second_level_key: two on top and second_level_key on bottom
  three:
    second_level_key: three on top and second_level_key on bottom


When substituting multiple list values into the same string
````````````````````````````````````````````````````````````

This is interpreted as a dot product. Yamlicious will substitute every
combination of variables between the two lists.

If ``BOYS=joey,johnny,bobby`` and ``GIRLS=sally,mary`` then:

.. code-block:: yaml

  "$(BOYS) likes $(GIRLS)"

becomes:

.. code-block:: yaml

  - joey likes sally
  - joey likes mary
  - johnny likes sally
  - johnny likes mary
  - bobby likes sally
  - bobby likes mary

Note -- the rest of the "positional" list substitution rules (defined in the
immediately previous sections) apply to dot product substitutions.


Load Another File
----------------------

Sometimes, it makes sense to define sub-configuration somewhere outside the
main configuration file. (e.g., secrets go somewhere special.) Yamlicious gives
you the `insert`_ key to accomplish this.

Note: `insert_` is a *functional feature key*. (Defined more in the `Functional
Feature Keys`_ section.) These are keys that participate in something like a
function call -- the entire map that contains a functional key evaluates to
functional behavior applied to the key's value. (No project is complete without
a smidge of functional programming.) You can only use one of these keys in a
map at a time because yamlicious replaces the key-containing map with a
document -- the result of the function applied to the key's value. Multiple
keys is an abiguous definition.

.. code-block:: yaml

  some_place:
    placed_here:
      _insert: other/file.yaml

In this case, the rendered YAML output of ``other/file.yaml`` is placed under
the ``placed_here`` key.

.. code-block:: yaml

  some_place:
    placed_here:
      contents of:
        - that other file
        - which can be arbitrary YAML

You can use variable substitution with the `insert`_ feature to get conditional
configuration.

.. code-block:: yaml

  user_settings:
    _insert: $(USER)/conf.yaml


Merge
---------------

Yamlicious allows you to *merge* an external file into a bit of config.

.. code-block:: yaml

  merged_settings:
    _merge:
      - some_list: ['thing']
        some_thing: 'thing'

      - _insert: some_other_place.yaml

When you ask Yamlicious to do this, it will use a strategy I call *safe deep merge
with list append*. Yamlicious merges dictionaries recursively by combining their
key-value pairs. It merges lists by list addition. It refuses, however, to
merge anything else. (Anything else would be shoot-self-in-foot territory, and
I'd rather not encourage it.)

if ``some_other_place.yaml`` looked like this:

.. code-block:: yaml

  some_list: ['second_thing']
  some_other_thing: 'thing'


The above configuration would render as follows:

.. code-block:: yaml

  merged_settings:
    some_list: ['thing', 'second_thing']
    some_thing: 'thing'
    some_other_thing: 'thing'

If you're looking to implement the common *default override* pattern, specify
`The Default Document`_ as part of the Yamlicious API. That feature is specifically
built to help you not have to allow arbitrary overrides when including files.
If you absolutely must allow overrides, use the `merge_override`_ keyword,
but note that it is turned off by default.

Insert and Merge
------------------

Loading several files and merging them is a common pattern, and it would be
nice if folks didn't have to be verbose if that's the behavior they're looking
for. This is what the `insert_merge`_ key is for.

.. code-block:: yaml

  merged_stuff:
    _insert_merge:
      - first/place.yaml
      - second/place.yaml
      - third/place.yaml

This key will load each file in order and merge that file into the previous
file.



Merging Entire Documents
-------------------------

If you'd like to merge an entire document with your own, use the `include`_
feature key.

Note: `include`_ is a *document feature key*. (Defined more in the `Document
Feature Keys`_ section.) Unlike functional feature keys, which apply behavior
to any map embedded anywhere in the document hierarchy, document feature keys
apply behavior to the entire document, and therefore must exist at the top of
the YAML document.

.. code-block:: 


Changing the Environment
-------------------------

You can also use the `env`_ document key to place new variables into the
environment.

.. code-block:: yaml

  _env:
    COOLEST_PERSON: kyle

These variables can be used either in *the same document* (although the utility
of that is not immediately obvious, other than for mitigating DRY violation)
or, more importantly, *in documents that include it*. Yamlicious supports this
by taking special care to re-run string substitution each time it changes a
document's environment. (Remember, string substitution is idempotent.)

This behavior is somewhat dangerous if the included document defines a variable
that's already defined in the including document. If the including document
uses string subtitution to define included document paths, those substitutions
can happen using only the *initial* version of the environment (before it is
mutated by the act of inclusion). If the included document then changes any key
that's used in the process of inclusion, things get hard to reason about.

Rather than allow such craziness, Yamlicious bans it. That is, it does not
allow multiple documents included in the same parent document to define
differing versions of the same environment variable. It does allow actual
environment variables to coexist with (and override) those defined in `env`_.
Not allowing this would be brittle and would remove a very common use case,
where setting an environment variable changes some sort of important behavior.


The Default Document
---------------------

Yamlicious merge-overrides the configuration document it renders with a
*default document* that it is configured to use.

This is the only place that, by default, uses the merge-override (rather than
safe merge) behavior. For that reason, it's best to use the default document
feature to specify override behavior. If you're wanting override behavior that
can't be done by using the default document, chances are you're doing something
that's either too complex or wrong. If you insist, there's always
`merge_override`_.


Functional Conditional Keys
---------------------------------

To specify a condition in-line, you can use the *functional conditional*
feature keys (`case`_ and `cond`_), each inspired by Lisp. This adds a bit too
much Turing completeness to the project for the taste of most, so these are
disabled by default.

.. code-block:: yaml

  case_configuration:
    '_case':
      - '$(USER)'
      - {'kyle': 'is awesome'}
      - {'_otherwise': 'is not awesome'}
  cond_configuration:
    '_cond':
      - {"$(ENV) in ['test', 'prod']": 'go!'}
      - {true: 'undefined'}

Note the use of the python expression. This is mostly for convenience and
terseness. Nobody wants to write a boolean expression in YAML, and I don't
particularly want to implement it, either, so Yamlicious ``eval()`` s every single
string that it finds below either functional conditional key.


List substitution works in both kinds of functional conditional. For example,
if ``GOOD_USERS=kyle,anthony``, then the following expression

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'$(GOOD_USERS)': 'go!'}
      - {'_otherwise':  'stay. :('}

evaluates to

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'kyle': 'go!',
         'anthony': 'go!'}
      - ['_otherwise',  'stay. :(']

Yamlicious is careful to "do the right thing" here. While there is no defined
order in how it matches either the key ``'anthony'`` or ``'kyle'``, it will try
to match both before falling back to the `otherwise`_ key.

Be careful to not do something like this unless you really mean it:

.. code-block:: yaml

  access_configuration:
    '_case':
      - {'$(GOOD_USERS)': '$(_KEY)'}
      - {'_otherwise':  'stay. :('}

While it will technically work, Yamlicious offers no definition for what the
above expression evaluates to -- the order of iteration for a map/dictionary is
an implementation detail.


Lazy Loading
--------------

If you notice an explosion in the number of Yamlicious files that your program
includes, and you also notice that only a few of them ever get used, you'll
likely want to conditionally load said files only when they're needed. Yamlicious
provides two lazy loading keys to help you with this.

The `lazy`_ key changes nothing about the semantic meaning of the document it
points to. It does change the time when functional key evaluation happens.
Yamlicious evaluates embedded functional keys at *lookup time*, rather than
during the depth-first functional key evaluation of the entire document.

In this example

.. code-block:: yaml

  _lazy:
    one:
      _insert: some/other/file.yaml

The `insert`_ evaluation happens only when someone tries to look at the
``one`` key.

The `lazy_lookup`_ key delays functional key evaluation just like `lazy`_, and
it also allows you to use string substitution of the special variable
``$(_KEY)`` to define how every key in the document is looked up. Rather than
defining a document for *every key* in the map, you define *one expression*
that, after string subtitution, can evaluate to *any key*.

To get the most power, pair lazy lookup with file inclusion. Here's an example
inspired by YAML configuration of SQL tables.

.. code-block:: yaml

  tables:
    _lazy_lookup:
      _insert_merge:
        - generic/schema/$(_KEY).table.yaml
        - $(SYSTEM)/schema/$(_KEY).table.yaml
        - $(INSTITUTION)/schema/$(_KEY).table.yaml

Note that there's nothing that prevents lazy-loaded documents from merging with
one another. If you're feeling particularly masochistic, you can define this
confusing yet equivalent thing.

.. code-block:: yaml

  tables:
    _merge:
      - _lazy_lookup:
          _insert_merge:
            - generic/schema/$(_KEY).table.yaml
            - $(SYSTEM)/schema/$(_KEY).table.yaml
      - _lazy_lookup:
          _insert_merge:
            - $(INSTITUTION)/schema/$(_KEY).table.yaml

Order Of Operations
====================

Yamlicious goes through the following phases when processing a document:

1. String substitution.
2. Document key evaluation.
3. String substitution.
4. Functional key evaluation (depth-first).


Feature Key Definitions
========================

Enough with your words. Let's define this stuff explicitly.

Document Feature Keys
------------------------

These keys must be placed at the *top* level of a document, and affect the
entire document that they're placed inside. They disappear when rendered.


env 
````````````````````````````````

.. code-block:: yaml

  _env:
    <variable>: <value>
    ...

Sets document environment variables to given values.

include
`````````````````

.. code-block:: yaml

  _include:
    - <file-path>
    - <file-path>
    - ...

Loads and safe-merges several files into the document.


Functional Feature Keys
------------------------

The key must exist by itself in its containing dictionary. The feature key,
itself, describes a transformation operation on the given document. 

.. code-block:: yaml

  _<feature-key>: <document>



insert
````````````````````````````````

.. code-block:: yaml

  _insert <file-path>

Evaluates to the loaded and processed configuration document found at
``file_path``.


merge
````````````````````````````````

.. code-block:: yaml

  _merge: [ <document>, <document>, ... ]

Uses safe-merge-with-list-append to merge given documents together. Can safely
merge dictionaries and lists, but nothing else.


merge_override
````````````````````````````````

.. code-block:: yaml

  _merge_override: [ <document>, <document>, ... ]

Uses deep-merge to merge given documents together. Can safely merge anything.
For scalar values, documents further down the list override documents earlier
in the list.


insert_merge
````````````````````````````````

.. code-block:: yaml

  _insert_merge [ <file-path>, <file-path>, ... ]

Loads files and then merges them with safe-merge-with-list-append.


case
````````````````````````````````
(NOT IMPLEMENTED)

.. code-block:: yaml

  '_case':
    - <key-python-expression>
    - {<match-python-expression>, <outcome-python-expression>}
    ...

Functional case. Evaluates to the first outcome expression whose match
expression is python-equal to the key expression.


otherwise
````````````````````````````````
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_otherwise': <expression>

Evaluates to a case condition that always matches.


cond
````````````````````````````````
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_cond':
      - {<boolean-python-expression>, <outcome-python-expression>}
      ...

Functional cond. Evaluates to the first outcome expression whose boolean
expression is true.


lazy
````````````````````````````````
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_lazy': <document>

Evaluates to document, but where each of the keys in document is lazy-loaded.


lazy_lookup
````````````````````````````````
(NOT IMPLEMENTED)

.. code-block:: yaml

    '_lazy_lookup': <value-expression>

Evaluates to a lazy-loaded dictionary, where every key is evaluated at lookup
time by evaluating the value-expression, which is allowed to use the ``_KEY``
environment variable


The Validator
==============

TBD

The Command
====================

Yamlicious comes with a convenient command, ``yamlicious``, that reads input
from stdin and writes to stdout. It uses a default configuration, along with
all environment variables, in order to process the yaml document fed to it on
standard in::

  [10:49:46][kderr@Kyles-MacBook-Pro][~/Repositories/derrley/yamlicious]
  $ cat /tmp/test
  Hello: "$(PWD) is the current wd"


  [10:49:52][kderr@Kyles-MacBook-Pro][~/Repositories/derrley/yamlicious]
  $ cat /tmp/test | yamlicious
  {Hello: /Users/kderr/Repositories/derrley/yamlicious is the current wd}


The API
=================

TBD

Custom Feature Keys
====================

TBD
